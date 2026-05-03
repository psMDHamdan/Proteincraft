"""
Structure prediction via ESMFold (HuggingFace Inference API or ESM Atlas API).
Returns PDB string and per-residue pLDDT confidence scores.
"""

from __future__ import annotations

import logging
import re

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def predict_structure(sequence: str) -> dict:
    """
    Fold a protein sequence using the ESMFold endpoint.

    Tries:
        1. ESM Metagenomic Atlas fold API (no auth required, rate-limited).
        2. HuggingFace Inference API for facebook/esmfold_v1 (requires HF_API_TOKEN).

    Args:
        sequence: Amino acid sequence (max ~400 aa recommended for Atlas API).

    Returns:
        Dict with keys: pdb_string, mean_plddt, min_plddt, max_plddt, confidence_note.
    """
    pdb_string = await _try_esmatlas(sequence)

    if not pdb_string and settings.hf_api_token:
        pdb_string = await _try_hf_inference(sequence)

    if not pdb_string:
        raise RuntimeError(
            "ESMFold prediction failed. "
            "Provide HF_API_TOKEN in .env or use a shorter sequence (<400 aa) for the Atlas API."
        )

    plddt_scores = _parse_plddt(pdb_string)
    mean_plddt = sum(plddt_scores) / len(plddt_scores) if plddt_scores else 0.0

    confidence_note = _confidence_note(mean_plddt)

    return {
        "pdb_string": pdb_string,
        "mean_plddt": round(mean_plddt, 2),
        "min_plddt": round(min(plddt_scores, default=0.0), 2),
        "max_plddt": round(max(plddt_scores, default=0.0), 2),
        "confidence_note": confidence_note,
    }


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------

async def _try_esmatlas(sequence: str) -> str | None:
    """Call the ESM Metagenomic Atlas fold API."""
    url = settings.esmfold_api_url  # https://api.esmatlas.com/foldSequence/v1/pdb
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        async with httpx.AsyncClient(timeout=settings.esmfold_timeout) as client:
            resp = await client.post(url, content=sequence, headers=headers)
            if resp.status_code == 200 and resp.text.startswith("ATOM"):
                logger.info("ESM Atlas fold succeeded for sequence length %d", len(sequence))
                return resp.text
            else:
                logger.warning(
                    "ESM Atlas API returned %d: %s", resp.status_code, resp.text[:200]
                )
    except httpx.TimeoutException:
        logger.warning("ESM Atlas fold request timed out.")
    except Exception as exc:
        logger.warning("ESM Atlas fold error: %s", exc)
    return None


async def _try_hf_inference(sequence: str) -> str | None:
    """Call HuggingFace Inference API for facebook/esmfold_v1."""
    url = "https://api-inference.huggingface.co/models/facebook/esmfold_v1"
    headers = {
        "Authorization": f"Bearer {settings.hf_api_token}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=settings.esmfold_timeout) as client:
            resp = await client.post(url, json={"inputs": sequence}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                # HF returns PDB as plain text in the response
                if isinstance(data, str) and data.startswith("ATOM"):
                    return data
                # Some versions wrap in a list
                if isinstance(data, list) and data:
                    return str(data[0])
                logger.warning("Unexpected HF ESMFold response format: %s", str(data)[:200])
            else:
                logger.warning("HF Inference API %d: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("HF Inference fold error: %s", exc)
    return None


# ---------------------------------------------------------------------------
# PDB parsing helpers
# ---------------------------------------------------------------------------

_ATOM_RE = re.compile(r"^ATOM\s+\d+\s+CA\s+\w+\s+\w\s+\d+\s+[\d\-\.]+\s+[\d\-\.]+\s+[\d\-\.]+\s+[\d\.]+\s+([\d\.]+)")


def _parse_plddt(pdb_string: str) -> list[float]:
    """
    Extract per-residue pLDDT scores from the B-factor column of CA ATOM records.
    """
    scores: list[float] = []
    for line in pdb_string.splitlines():
        m = _ATOM_RE.match(line)
        if m:
            try:
                scores.append(float(m.group(1)))
            except ValueError:
                pass
    return scores


def _confidence_note(mean_plddt: float) -> str:
    if mean_plddt >= 90:
        return "Very high confidence (pLDDT ≥ 90): likely accurate backbone."
    if mean_plddt >= 70:
        return "High confidence (pLDDT 70–90): good for most residues."
    if mean_plddt >= 50:
        return "Low confidence (pLDDT 50–70): disordered regions likely."
    return "Very low confidence (pLDDT < 50): treat as unreliable."
