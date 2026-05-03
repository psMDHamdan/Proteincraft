"""
Sequence optimization and ranking layer.
Ranks candidate sequences by diversity, stability proxy, and ESM heuristic scores.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.utils.scoring import diff_mutations, mean_pairwise_hamming


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class RankedSequence:
    sequence: str
    mutations_from_input: list[str] = field(default_factory=list)
    esm_score: float = 0.0
    stability_proxy: float = 0.0
    diversity_score: float = 0.0
    heuristic_score: float = 0.0
    rank: int = 0


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def stability_proxy(instability_index: float, isoelectric_point: float) -> float:
    """
    Heuristic stability proxy in [0, 1].

    - Instability index < 40 → stable (Guruprasad et al.)
    - pI near physiological (6.5–7.5) → mildly favoured for solubility.

    Returns higher values for more stable sequences.
    """
    # Instability component: sigmoid centred at 40, inverted
    stability_score = 1.0 / (1.0 + math.exp((instability_index - 40.0) / 8.0))

    # pI component: gaussian centred at 7.0, width ~2
    pi_score = math.exp(-((isoelectric_point - 7.0) ** 2) / (2 * 2.0**2))

    return round(0.7 * stability_score + 0.3 * pi_score, 4)


def diversity_score(sequence: str, population: list[str]) -> float:
    """
    Diversity score for a single sequence relative to a population.

    Returns the mean Hamming distance to all other sequences, normalised to [0, 1].
    """
    if not population:
        return 1.0
    distances = []
    for other in population:
        min_len = min(len(sequence), len(other))
        dist = sum(a != b for a, b in zip(sequence[:min_len], other[:min_len]))
        distances.append(dist / min_len if min_len else 0.0)
    return round(sum(distances) / len(distances), 4)


def heuristic_score(
    esm_score: float,
    stab_proxy: float,
    div_score: float,
    weights: tuple[float, float, float] = (0.5, 0.3, 0.2),
) -> float:
    """
    Combined heuristic score (higher = better).

    Weights: (esm_weight, stability_weight, diversity_weight).
    ESM score is normalised by mapping from [-∞, 0] range using tanh.
    """
    esm_weight, stab_weight, div_weight = weights

    # Map ESM PLL (negative float) to [0, 1]: more negative → lower score
    # Typical PLL per token: -0.1 to -5.0
    esm_norm = (math.tanh(esm_score / 2.0) + 1.0) / 2.0

    score = esm_weight * esm_norm + stab_weight * stab_proxy + div_weight * div_score
    return round(score, 4)


# ---------------------------------------------------------------------------
# Main ranking pipeline
# ---------------------------------------------------------------------------

def rank_sequences(
    sequences: list[str],
    input_sequence: str,
    properties_map: dict[str, dict],
    esm_scores: dict[str, float],
    top_k: int = 10,
) -> list[RankedSequence]:
    """
    Rank candidate sequences using diversity, stability proxy, and ESM scores.

    Args:
        sequences: List of candidate amino acid sequences.
        input_sequence: Original input sequence (for mutation diffing).
        properties_map: Dict mapping sequence → property dict
                        (keys: instability_index, isoelectric_point).
        esm_scores: Dict mapping sequence → PLL score float.
        top_k: Maximum number of sequences to return.

    Returns:
        Sorted list of RankedSequence objects (best first).
    """
    ranked: list[RankedSequence] = []

    for seq in sequences:
        props = properties_map.get(seq, {})
        esm = esm_scores.get(seq, -5.0)

        # Compute mutation list vs. input
        min_len = min(len(seq), len(input_sequence))
        mutations = diff_mutations(input_sequence[:min_len], seq[:min_len])

        # Diversity relative to the rest of the candidate pool
        others = [s for s in sequences if s != seq]
        div = diversity_score(seq, others)

        # Stability proxy
        stab = stability_proxy(
            props.get("instability_index", 50.0),
            props.get("isoelectric_point", 7.0),
        )

        # Combined heuristic
        h_score = heuristic_score(esm, stab, div)

        ranked.append(
            RankedSequence(
                sequence=seq,
                mutations_from_input=mutations,
                esm_score=round(esm, 4),
                stability_proxy=stab,
                diversity_score=div,
                heuristic_score=h_score,
            )
        )

    # Sort descending by heuristic score
    ranked.sort(key=lambda r: r.heuristic_score, reverse=True)

    # Assign ranks
    for i, r in enumerate(ranked):
        r.rank = i + 1

    return ranked[:top_k]
