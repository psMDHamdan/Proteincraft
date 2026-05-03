"""
ESM2 service: embeddings, pseudo-log-likelihood scoring, masked variant generation.
Model: facebook/esm2_t33_650M_UR50D
"""

from __future__ import annotations

import logging
import math
from functools import lru_cache
from typing import Any

import numpy as np
import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def _load_model() -> tuple[Any, Any]:
    """Load ESM2 tokenizer and model once; cache for the process lifetime."""
    logger.info("Loading ESM2 model: %s", settings.esm_model_name)
    tokenizer = AutoTokenizer.from_pretrained(settings.esm_model_name)
    model = AutoModelForMaskedLM.from_pretrained(settings.esm_model_name)
    device = torch.device(settings.esm_device)
    model = model.to(device)
    model.eval()
    logger.info("ESM2 model loaded on device: %s", device)
    return tokenizer, model


def _device() -> torch.device:
    return torch.device(settings.esm_device)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_embeddings(sequence: str) -> np.ndarray:
    """
    Extract mean-pooled sequence embedding from ESM2.

    Args:
        sequence: Amino acid sequence (single-letter code).

    Returns:
        1-D numpy array of shape (hidden_size,).
    """
    tokenizer, model = _load_model()
    inputs = tokenizer(sequence, return_tensors="pt").to(_device())

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)

    # Last hidden state: [batch, seq_len, hidden]
    hidden = outputs.hidden_states[-1]  # type: ignore[index]

    # Mask out [CLS] and [EOS] tokens (indices 0 and -1)
    token_repr = hidden[0, 1:-1, :]
    embedding = token_repr.mean(dim=0).cpu().numpy()
    return embedding


def score_sequence(sequence: str) -> float:
    """
    Compute pseudo-log-likelihood (PLL) for a sequence using masked scoring.

    Each position is masked in turn; the model predicts the log-probability
    of the true amino acid.  The sum gives the PLL.

    Args:
        sequence: Amino acid sequence.

    Returns:
        Float PLL score (higher = more plausible under the model).
    """
    tokenizer, model = _load_model()
    tokens = tokenizer(sequence, return_tensors="pt").to(_device())
    input_ids = tokens["input_ids"].clone()

    # Positions to score (exclude [CLS]=0 and [EOS]=-1)
    seq_len = input_ids.shape[1] - 2  # non-special tokens
    pll = 0.0

    with torch.no_grad():
        for i in range(1, seq_len + 1):
            masked = input_ids.clone()
            masked[0, i] = tokenizer.mask_token_id
            out = model(input_ids=masked, attention_mask=tokens["attention_mask"])
            logits = out.logits[0, i]  # vocab logits at masked position
            log_probs = torch.log_softmax(logits, dim=-1)
            true_token = input_ids[0, i].item()
            pll += log_probs[true_token].item()

    return pll / seq_len  # normalised by length


def generate_masked_variants(
    sequence: str,
    positions: list[int] | None = None,
    top_k: int = 5,
    max_mutations: int = 3,
) -> list[str]:
    """
    Generate candidate sequences by masking positions and sampling top-k predictions.

    Args:
        sequence: Wild-type amino acid sequence.
        positions: 0-based positions to consider for mutation.
                   If None, selects top-``max_mutations`` lowest-likelihood positions.
        top_k: Number of candidate sequences to return.
        max_mutations: Maximum simultaneous positions to mutate.

    Returns:
        List of candidate amino acid sequences (may include wild-type).
    """
    tokenizer, model = _load_model()

    if positions is None:
        positions = _find_low_likelihood_positions(sequence, tokenizer, model, max_mutations)

    # Mask all selected positions simultaneously
    inputs = tokenizer(sequence, return_tensors="pt").to(_device())
    input_ids = inputs["input_ids"].clone()

    # Convert 0-based seq positions to token positions (+1 for [CLS])
    token_positions = [p + 1 for p in positions if 0 <= p < len(sequence)]

    for tp in token_positions:
        input_ids[0, tp] = tokenizer.mask_token_id

    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=inputs["attention_mask"])

    # For each masked position grab top-k predictions
    aa_vocab = _aa_token_ids(tokenizer)
    candidates: list[str] = []

    # Start with the wild-type tokens
    base_tokens = tokenizer(sequence, return_tensors="pt")["input_ids"][0].tolist()

    # Build combinations greedily: vary one position at a time
    for tp, orig_pos in zip(token_positions, positions):
        logits = out.logits[0, tp]
        aa_logits = {tid: logits[tid].item() for tid in aa_vocab}
        top_tokens = sorted(aa_logits, key=aa_logits.get, reverse=True)[:top_k]  # type: ignore[arg-type]

        for tt in top_tokens:
            new_tokens = base_tokens[:]
            new_tokens[tp] = tt
            decoded = tokenizer.decode(new_tokens[1:-1], skip_special_tokens=True)
            decoded = decoded.replace(" ", "")  # ESM tokenizer adds spaces
            if decoded != sequence:
                candidates.append(decoded)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        if c not in seen and len(c) == len(sequence):
            seen.add(c)
            unique.append(c)
            if len(unique) >= top_k:
                break

    return unique


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _find_low_likelihood_positions(
    sequence: str,
    tokenizer: Any,
    model: Any,
    n: int,
) -> list[int]:
    """Return the n positions with lowest per-position log-likelihood."""
    inputs = tokenizer(sequence, return_tensors="pt").to(_device())
    input_ids = inputs["input_ids"]
    scores: list[tuple[int, float]] = []

    with torch.no_grad():
        for i in range(1, len(sequence) + 1):
            masked = input_ids.clone()
            masked[0, i] = tokenizer.mask_token_id
            out = model(input_ids=masked, attention_mask=inputs["attention_mask"])
            log_probs = torch.log_softmax(out.logits[0, i], dim=-1)
            true_tok = input_ids[0, i].item()
            scores.append((i - 1, log_probs[true_tok].item()))  # 0-based pos

    scores.sort(key=lambda x: x[1])  # ascending: lowest log-prob first
    return [s[0] for s in scores[:n]]


def _aa_token_ids(tokenizer: Any) -> list[int]:
    """Return token IDs corresponding to the 20 standard amino acids."""
    aa_letters = list("ACDEFGHIKLMNPQRSTVWY")
    ids = []
    for aa in aa_letters:
        encoded = tokenizer.encode(aa, add_special_tokens=False)
        if encoded:
            ids.append(encoded[0])
    return list(set(ids))
