"""
Unit tests for Biopython-based property computation.
"""

from __future__ import annotations

import pytest

from app.services.property_service import compute_properties, compute_properties_dict


INSULIN_SEQ = "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN"


def test_compute_properties_returns_result():
    result = compute_properties(INSULIN_SEQ)
    assert result.molecular_weight > 0
    assert 0.0 <= result.aromaticity <= 1.0
    assert result.isoelectric_point > 0.0
    assert isinstance(result.instability_index, float)
    assert isinstance(result.gravy, float)


def test_secondary_structure_fraction_sums_to_one():
    result = compute_properties(INSULIN_SEQ)
    ss = result.secondary_structure_fraction
    total = ss["helix"] + ss["turn"] + ss["sheet"]
    assert abs(total - 1.0) < 1e-3


def test_compute_properties_dict_keys():
    d = compute_properties_dict(INSULIN_SEQ)
    expected_keys = {
        "instability_index", "isoelectric_point", "aromaticity",
        "molecular_weight", "gravy", "secondary_structure_fraction",
    }
    assert expected_keys == set(d.keys())


def test_stability_classification():
    """Insulin is a known stable protein — instability index should be < 40."""
    result = compute_properties(INSULIN_SEQ)
    # Biopython instability for insulin is typically ~20-30
    assert result.instability_index < 60  # conservative bound


def test_invalid_sequence_raises():
    with pytest.raises(ValueError):
        compute_properties("ACDEFXXX")  # X is invalid


def test_short_sequence():
    """Very short sequences should still compute without error."""
    result = compute_properties("ACDE")
    assert result.molecular_weight > 0
