"""
Unit tests for POST /predict-properties.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_SEQ = "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVS"


@pytest.fixture(autouse=True)
def mock_esm_score():
    with patch("app.services.esm_service.score_sequence", return_value=-1.2):
        yield


def test_predict_properties_ok():
    resp = client.post("/predict-properties", json={"sequence": SAMPLE_SEQ})
    assert resp.status_code == 200
    data = resp.json()
    assert "properties" in data
    props = data["properties"]
    assert "instability_index" in props
    assert "isoelectric_point" in props
    assert "molecular_weight" in props
    assert "aromaticity" in props
    assert "gravy" in props
    assert "esm2_score" in data
    assert data["length"] == len(SAMPLE_SEQ)


def test_predict_stability_assessment():
    resp = client.post("/predict-properties", json={"sequence": SAMPLE_SEQ})
    data = resp.json()
    assert data["stability_assessment"] in ("stable", "borderline", "unstable")


def test_predict_invalid_sequence():
    resp = client.post("/predict-properties", json={"sequence": "ACDEFXXX"})
    assert resp.status_code == 422


def test_predict_short_sequence():
    resp = client.post("/predict-properties", json={"sequence": "ACG"})
    assert resp.status_code == 422
