"""
POST /predict-properties — Property prediction + ESM scoring for a given sequence.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.protein import PredictRequest, PropertyResult
from app.services import esm_service, property_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict-properties", tags=["Predict"])


@router.post(
    "",
    response_model=dict,
    summary="Predict biophysical properties and ESM2 score for a sequence",
)
async def predict_properties(request: PredictRequest) -> dict:
    """
    Compute biophysical properties (instability index, pI, aromaticity, MW, GRAVY,
    secondary structure) and ESM2 pseudo-log-likelihood for the input sequence.
    """
    try:
        props_task = asyncio.to_thread(
            property_service.compute_properties_dict, request.sequence
        )
        esm_task = asyncio.to_thread(esm_service.score_sequence, request.sequence)

        props, esm_score = await asyncio.gather(props_task, esm_task)

        return {
            "sequence": request.sequence,
            "length": len(request.sequence),
            "properties": props,
            "esm2_score": round(esm_score, 4),
            "stability_assessment": _stability_assessment(
                props.get("instability_index", 50.0)
            ),
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Property prediction failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        )


def _stability_assessment(instability_index: float) -> str:
    if instability_index < 40:
        return "stable"
    if instability_index < 60:
        return "borderline"
    return "unstable"
