"""
Biophysical property prediction using Biopython.
Extensible via BasePredictor for plug-in ML predictors.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from Bio.SeqUtils.ProtParam import ProteinAnalysis

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PropertyResult:
    instability_index: float
    isoelectric_point: float
    aromaticity: float
    molecular_weight: float
    gravy: float
    secondary_structure_fraction: dict[str, float]  # helix, turn, sheet


# ---------------------------------------------------------------------------
# Extensibility hook
# ---------------------------------------------------------------------------

class BasePredictor(ABC):
    """Abstract base for plug-in ML-based property predictors."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def predict(self, sequence: str) -> dict[str, float]:
        """Return a dict of property_name -> float for the given sequence."""
        ...


# Registry for external predictors
_predictor_registry: list[BasePredictor] = []


def register_predictor(predictor: BasePredictor) -> None:
    """Register a custom ML predictor."""
    _predictor_registry.append(predictor)
    logger.info("Registered custom predictor: %s", predictor.name)


# ---------------------------------------------------------------------------
# Core property computation
# ---------------------------------------------------------------------------

def compute_properties(sequence: str) -> PropertyResult:
    """
    Compute biophysical properties using Biopython ProteinAnalysis.

    Args:
        sequence: Amino acid sequence (standard 20 aa).

    Returns:
        PropertyResult dataclass.

    Raises:
        ValueError: If sequence contains non-standard amino acids.
    """
    # Biopython does not accept non-standard residues gracefully
    cleaned = sequence.strip().upper()

    try:
        analysis = ProteinAnalysis(cleaned)
        ss_frac = analysis.secondary_structure_fraction()
        return PropertyResult(
            instability_index=analysis.instability_index(),
            isoelectric_point=analysis.isoelectric_point(),
            aromaticity=analysis.aromaticity(),
            molecular_weight=analysis.molecular_weight(),
            gravy=analysis.gravy(),
            secondary_structure_fraction={
                "helix": round(ss_frac[0], 4),
                "turn": round(ss_frac[1], 4),
                "sheet": round(ss_frac[2], 4),
            },
        )
    except Exception as exc:
        raise ValueError(f"Property computation failed: {exc}") from exc


def compute_properties_dict(sequence: str) -> dict:
    """Convenience wrapper returning a plain dict (for JSON serialisation)."""
    result = compute_properties(sequence)
    return {
        "instability_index": round(result.instability_index, 4),
        "isoelectric_point": round(result.isoelectric_point, 4),
        "aromaticity": round(result.aromaticity, 4),
        "molecular_weight": round(result.molecular_weight, 2),
        "gravy": round(result.gravy, 4),
        "secondary_structure_fraction": result.secondary_structure_fraction,
    }


def run_all_predictors(sequence: str) -> dict[str, dict[str, float]]:
    """
    Run all registered external predictors on the given sequence.

    Returns:
        Dict keyed by predictor name, each value is the predictor's output dict.
    """
    results: dict[str, dict[str, float]] = {}
    for predictor in _predictor_registry:
        try:
            results[predictor.name] = predictor.predict(sequence)
        except Exception as exc:
            logger.warning("Predictor '%s' failed: %s", predictor.name, exc)
            results[predictor.name] = {"error": str(exc)}
    return results
