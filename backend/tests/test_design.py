"""
Integration tests for POST /design-sequence.
ESM2 and Gemini are mocked to avoid network/GPU dependency in CI.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_SEQ = "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISGSGGSTYYADS"


@pytest.fixture(autouse=True)
def mock_esm():
    with (
        patch("app.services.esm_service.generate_masked_variants") as mock_gen,
        patch("app.services.esm_service.score_sequence") as mock_score,
    ):
        mock_gen.return_value = [SAMPLE_SEQ, SAMPLE_SEQ[::-1][:len(SAMPLE_SEQ)]]
        mock_score.return_value = -1.5
        yield mock_gen, mock_score


@pytest.fixture(autouse=True)
def mock_gemini():
    with (
        patch("app.services.gemini_service.rank_sequences") as mock_rank,
        patch("app.services.gemini_service.explain_design") as mock_explain,
    ):
        mock_rank.side_effect = lambda candidates, context: [
            {**c, "gemini_rank": i + 1, "gemini_rationale": "test"} for i, c in enumerate(candidates)
        ]
        mock_explain.return_value = "Test explanation from Gemini."
        yield mock_rank, mock_explain


@pytest.fixture(autouse=True)
def mock_db():
    """Stub the database session so tests don't require PostgreSQL."""
    from unittest.mock import AsyncMock
    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.add = MagicMock()

    with patch("app.routes.design.get_db") as mock_get_db:
        async def _gen():
            yield mock_session
        mock_get_db.return_value = _gen()
        yield mock_session


def test_design_sequence_raw():
    payload = {"sequence": SAMPLE_SEQ, "top_k": 2}
    resp = client.post("/design-sequence", json=payload)
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert "job_id" in data
    assert "designed_sequences" in data
    assert data["status"] == "complete"


def test_design_sequence_with_mutations():
    payload = {
        "sequence": SAMPLE_SEQ,
        "mutation_list": ["E1Q"],
        "top_k": 2,
    }
    resp = client.post("/design-sequence", json=payload)
    assert resp.status_code in (200, 201), resp.text


def test_design_sequence_fasta():
    fasta = f">test_protein\n{SAMPLE_SEQ}\n"
    payload = {"fasta_content": fasta, "top_k": 2}
    resp = client.post("/design-sequence", json=payload)
    assert resp.status_code in (200, 201), resp.text


def test_design_sequence_invalid_aa():
    payload = {"sequence": "EVQLVESXGGGL"}  # X is invalid
    resp = client.post("/design-sequence", json=payload)
    assert resp.status_code == 422


def test_design_sequence_empty():
    resp = client.post("/design-sequence", json={})
    assert resp.status_code == 422


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
