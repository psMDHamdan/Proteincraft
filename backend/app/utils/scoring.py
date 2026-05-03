"""Sequence distance and scoring utilities."""

from __future__ import annotations


def hamming_distance(seq1: str, seq2: str) -> int:
    """Compute Hamming distance between two equal-length sequences."""
    if len(seq1) != len(seq2):
        raise ValueError("Sequences must be the same length for Hamming distance.")
    return sum(a != b for a, b in zip(seq1, seq2))


def hamming_similarity(seq1: str, seq2: str) -> float:
    """Normalized Hamming similarity in [0, 1]."""
    if not seq1:
        return 1.0
    return 1.0 - hamming_distance(seq1, seq2) / len(seq1)


def mean_pairwise_hamming(sequences: list[str]) -> float:
    """Mean pairwise Hamming distance across a set of sequences."""
    n = len(sequences)
    if n < 2:
        return 0.0
    total = 0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            s1, s2 = sequences[i], sequences[j]
            min_len = min(len(s1), len(s2))
            total += hamming_distance(s1[:min_len], s2[:min_len])
            count += 1
    return total / count if count else 0.0


def levenshtein_distance(s1: str, s2: str) -> int:
    """Standard Levenshtein edit distance."""
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[j] = prev[j - 1]
            else:
                dp[j] = 1 + min(prev[j], dp[j - 1], prev[j - 1])
    return dp[n]


def diff_mutations(original: str, mutated: str) -> list[str]:
    """Return a list of mutation strings 'A23V' comparing original vs mutated."""
    mutations = []
    for i, (o, m) in enumerate(zip(original, mutated)):
        if o != m:
            mutations.append(f"{o}{i + 1}{m}")
    return mutations
