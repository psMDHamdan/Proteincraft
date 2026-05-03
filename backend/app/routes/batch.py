"""
POST /batch-design — Async batch processing of multiple design requests.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas.protein import BatchDesignRequest, BatchDesignResponse, ProteinResponse
from app.routes.design import design_sequence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/batch-design", tags=["Batch"])
settings = get_settings()


@router.post(
    "",
    response_model=BatchDesignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch protein sequence design (up to 50 requests)",
)
async def batch_design(
    request: BatchDesignRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchDesignResponse:
    """
    Process multiple design requests concurrently, respecting BATCH_CONCURRENCY setting.
    Returns ranked results for all requests.
    """
    semaphore = asyncio.Semaphore(settings.batch_concurrency)

    async def _safe_design(req) -> ProteinResponse | None:
        async with semaphore:
            try:
                return await design_sequence(req, db)
            except HTTPException as exc:
                logger.warning("Batch item failed with HTTP %d: %s", exc.status_code, exc.detail)
                return None
            except Exception as exc:
                logger.exception("Batch item failed: %s", exc)
                return None

    tasks = [_safe_design(req) for req in request.requests]
    results_raw = await asyncio.gather(*tasks)
    results = [r for r in results_raw if r is not None]

    return BatchDesignResponse(total=len(results), results=results)
