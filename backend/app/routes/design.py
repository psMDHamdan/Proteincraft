"""
POST /design-sequence — Core protein design endpoint.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.protein import ProteinJob
from app.schemas.protein import DesignRequest, ProteinResponse, RankedSequence
from app.services import esm_service, gemini_service, optimizer, property_service
from app.utils.fasta import apply_mutations, parse_fasta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/design-sequence", tags=["Design"])


@router.post(
    "",
    response_model=ProteinResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Design optimised protein sequences",
)
async def design_sequence(
    request: DesignRequest,
    db: AsyncSession = Depends(get_db),
) -> ProteinResponse:
    """
    Accept a raw sequence, FASTA content, or mutation list and return ranked
    candidate sequences with biophysical properties and a Gemini explanation.
    """
    # ── 1. Resolve input sequence ──────────────────────────────────────────
    input_sequence = _resolve_input_sequence(request)

    # ── 2. Create pending DB record ────────────────────────────────────────
    job = ProteinJob(
        id=uuid.uuid4(),
        input_sequence=input_sequence,
        mutation_list=request.mutation_list,
        target_antigen=request.target_antigen,
        desired_function=request.desired_function,
        status="processing",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()  # persist to get ID without committing

    try:
        # ── 3. Generate candidates via ESM2 ───────────────────────────────
        candidates_raw: list[str] = await asyncio.to_thread(
            esm_service.generate_masked_variants,
            input_sequence,
            None,
            request.top_k * 2,  # over-generate, then rank
            3,
        )
        # Always include the input sequence itself
        all_seqs = list({input_sequence, *candidates_raw})

        # ── 4. Score & properties in parallel ─────────────────────────────
        esm_scores, props_map = await _score_and_props(all_seqs)

        # ── 5. Rank sequences ─────────────────────────────────────────────
        ranked = optimizer.rank_sequences(
            sequences=all_seqs,
            input_sequence=input_sequence,
            properties_map=props_map,
            esm_scores=esm_scores,
            top_k=request.top_k,
        )

        # ── 6. Gemini ranking + explanation ───────────────────────────────
        candidates_dicts = [
            {
                "sequence": r.sequence,
                "esm_score": r.esm_score,
                "stability_proxy": r.stability_proxy,
                "diversity_score": r.diversity_score,
                "heuristic_score": r.heuristic_score,
                "mutations_from_input": r.mutations_from_input,
            }
            for r in ranked
        ]
        context = {
            "target_antigen": request.target_antigen,
            "desired_function": request.desired_function,
        }
        ranked_dicts = await asyncio.to_thread(
            gemini_service.rank_sequences, candidates_dicts, context
        )

        best_seq = ranked_dicts[0]["sequence"] if ranked_dicts else input_sequence
        best_props = props_map.get(best_seq, {})
        best_mutations = ranked_dicts[0].get("mutations_from_input", []) if ranked_dicts else []

        explanation = await asyncio.to_thread(
            gemini_service.explain_design,
            best_seq,
            best_props,
            best_mutations,
            request.desired_function,
        )

        # ── 7. Build response objects ─────────────────────────────────────
        ranked_sequences = [
            RankedSequence(
                sequence=d["sequence"],
                mutations_from_input=d.get("mutations_from_input", []),
                esm_score=d.get("esm_score", 0.0),
                stability_proxy=d.get("stability_proxy", 0.0),
                diversity_score=d.get("diversity_score", 0.0),
                heuristic_score=d.get("heuristic_score", 0.0),
                rank=d.get("gemini_rank", i + 1),
            )
            for i, d in enumerate(ranked_dicts)
        ]

        # ── 8. Build PropertyResult for best sequence ─────────────────────
        from app.schemas.protein import PropertyResult as PropSchema

        prop_schema: PropSchema | None = None
        if best_props:
            prop_schema = PropSchema(
                instability_index=best_props.get("instability_index", 0.0),
                isoelectric_point=best_props.get("isoelectric_point", 0.0),
                aromaticity=best_props.get("aromaticity", 0.0),
                molecular_weight=best_props.get("molecular_weight", 0.0),
                gravy=best_props.get("gravy", 0.0),
                secondary_structure_fraction=best_props.get(
                    "secondary_structure_fraction", {}
                ),
            )

        # ── 9. Persist results ────────────────────────────────────────────
        job.status = "complete"
        job.designed_sequences = [r.model_dump() for r in ranked_sequences]
        job.properties_json = best_props
        job.gemini_explanation = explanation
        job.updated_at = datetime.now(timezone.utc)

        return ProteinResponse(
            job_id=job.id,
            status="complete",
            input_sequence=input_sequence,
            designed_sequences=ranked_sequences,
            properties=prop_schema,
            gemini_explanation=explanation,
            created_at=job.created_at,
        )

    except Exception as exc:
        logger.exception("Design job %s failed: %s", job.id, exc)
        job.status = "failed"
        job.error_message = str(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Design failed: {exc}",
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_input_sequence(request: DesignRequest) -> str:
    """Resolve the canonical input sequence from the request."""
    if request.sequence:
        seq = request.sequence
    elif request.fasta_content:
        records = parse_fasta(request.fasta_content)
        seq = records[0].sequence  # use first record
    elif request.mutation_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="mutation_list provided without a base sequence. "
                   "Include 'sequence' or 'fasta_content'.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No input sequence provided.",
        )

    if request.mutation_list:
        seq = apply_mutations(seq, request.mutation_list)

    return seq


async def _score_and_props(
    sequences: list[str],
) -> tuple[dict[str, float], dict[str, dict]]:
    """Run ESM scoring and property prediction concurrently for all sequences."""

    async def _esm(seq: str) -> tuple[str, float]:
        try:
            score = await asyncio.to_thread(esm_service.score_sequence, seq)
        except Exception:
            score = -5.0
        return seq, score

    async def _props(seq: str) -> tuple[str, dict]:
        try:
            props = await asyncio.to_thread(property_service.compute_properties_dict, seq)
        except Exception:
            props = {}
        return seq, props

    esm_tasks = [_esm(s) for s in sequences]
    prop_tasks = [_props(s) for s in sequences]

    esm_results, prop_results = await asyncio.gather(
        asyncio.gather(*esm_tasks),
        asyncio.gather(*prop_tasks),
    )

    return dict(esm_results), dict(prop_results)
