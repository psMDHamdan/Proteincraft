"""
POST /structure — ESMFold structure prediction.
GET  /protein/{id} — Retrieve a stored protein job.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.protein import ProteinJob
from app.schemas.protein import StructureRequest, StructureResponse
from app.services import structure_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Structure & Retrieval"])


@router.post(
    "/structure",
    response_model=StructureResponse,
    summary="Predict 3D structure with ESMFold",
)
async def predict_structure(
    request: StructureRequest,
    db: AsyncSession = Depends(get_db),
) -> StructureResponse:
    """
    Submit an amino acid sequence to ESMFold and return the PDB string along
    with per-residue pLDDT confidence scores.
    """
    try:
        result = await structure_service.predict_structure(request.sequence)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Structure prediction failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Structure prediction failed: {exc}",
        )

    # Optionally store PDB in an existing job
    if request.job_id:
        try:
            job_uuid = uuid.UUID(request.job_id)
            stmt = select(ProteinJob).where(ProteinJob.id == job_uuid)
            job = (await db.execute(stmt)).scalar_one_or_none()
            if job:
                job.pdb_string = result["pdb_string"]
        except Exception as exc:
            logger.warning("Could not attach PDB to job %s: %s", request.job_id, exc)

    return StructureResponse(
        job_id=request.job_id,
        sequence=request.sequence,
        **result,
    )


@router.get(
    "/protein/{job_id}",
    response_model=dict,
    summary="Retrieve a protein design job by ID",
)
async def get_protein(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Retrieve stored results for a previously submitted protein design job.
    """
    stmt = select(ProteinJob).where(ProteinJob.id == job_id)
    job: ProteinJob | None = (await db.execute(stmt)).scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protein job '{job_id}' not found.",
        )

    return {
        "job_id": str(job.id),
        "status": job.status,
        "input_sequence": job.input_sequence,
        "mutation_list": job.mutation_list,
        "target_antigen": job.target_antigen,
        "desired_function": job.desired_function,
        "designed_sequences": job.designed_sequences,
        "properties": job.properties_json,
        "scores": job.scores_json,
        "pdb_available": job.pdb_string is not None,
        "gemini_explanation": job.gemini_explanation,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }
