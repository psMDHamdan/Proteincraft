"""
Gemini API service — used strictly as a reasoning, ranking, and explanation engine.
NOT used as a scientific predictor.
"""

from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _generate(prompt: str, temperature: float = 0.3) -> str:
    """Call Gemini and return the text response."""
    client = _get_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=2048,
        ),
    )
    return response.text or ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def rank_sequences(
    candidates: list[dict],
    context: dict | None = None,
) -> list[dict]:
    """
    Use Gemini to re-rank candidate sequences based on biophysical heuristics
    and contextual reasoning.

    Args:
        candidates: List of dicts with keys: sequence, esm_score, stability_proxy,
                    diversity_score, heuristic_score, mutations_from_input.
        context: Optional dict with keys: target_antigen, desired_function.

    Returns:
        List of candidates with added 'gemini_rank' and 'gemini_rationale' fields.
    """
    context_str = ""
    if context:
        if context.get("desired_function"):
            context_str += f"\nDesired function: {context['desired_function']}"
        if context.get("target_antigen"):
            context_str += f"\nTarget antigen (first 50 aa): {context['target_antigen'][:50]}..."

    candidates_json = json.dumps(
        [
            {
                "index": i,
                "sequence": c["sequence"][:30] + "..." if len(c["sequence"]) > 30 else c["sequence"],
                "esm_score": round(c.get("esm_score", 0), 4),
                "stability_proxy": round(c.get("stability_proxy", 0), 4),
                "diversity_score": round(c.get("diversity_score", 0), 4),
                "heuristic_score": round(c.get("heuristic_score", 0), 4),
                "mutations": c.get("mutations_from_input", []),
            }
            for i, c in enumerate(candidates)
        ],
        indent=2,
    )

    prompt = f"""You are a protein engineering expert assistant.
You are given a list of candidate protein sequences with computed biophysical scores.
Your role is to re-rank them using reasoning about protein engineering principles.

IMPORTANT: You are NOT a scientific predictor. Use the numeric scores as signals and apply
domain knowledge about sequence diversity, ESM model confidence, and stability proxies.
{context_str}

Candidates:
{candidates_json}

Respond ONLY with a JSON array (no markdown, no explanation text) in this exact format:
[
  {{"index": <original_index>, "gemini_rank": <1-based rank>, "gemini_rationale": "<brief reason>"}}
]

Rank from best (1) to worst. Every candidate must appear exactly once."""

    try:
        raw = _generate(prompt, temperature=0.2)
        # Strip potential markdown code fences
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        ranking = json.loads(raw)

        index_to_ranking = {r["index"]: r for r in ranking}
        for i, cand in enumerate(candidates):
            info = index_to_ranking.get(i, {})
            cand["gemini_rank"] = info.get("gemini_rank", i + 1)
            cand["gemini_rationale"] = info.get("gemini_rationale", "")

        candidates.sort(key=lambda x: x.get("gemini_rank", 9999))
    except Exception as exc:
        logger.warning("Gemini ranking failed, using heuristic order: %s", exc)
        for i, cand in enumerate(candidates):
            cand["gemini_rank"] = i + 1
            cand["gemini_rationale"] = "Ranked by heuristic score (Gemini unavailable)."

    return candidates


def explain_design(
    sequence: str,
    properties: dict,
    mutations: list[str],
    desired_function: str | None = None,
) -> str:
    """
    Generate a natural-language explanation of the designed sequence.

    Args:
        sequence: Designed amino acid sequence.
        properties: Dict of biophysical properties.
        mutations: List of mutations introduced.
        desired_function: Optional user-specified function.

    Returns:
        Plain-text explanation string.
    """
    props_str = json.dumps(
        {k: round(v, 3) if isinstance(v, float) else v for k, v in properties.items()},
        indent=2,
    )
    mut_str = ", ".join(mutations) if mutations else "no mutations (de novo)"
    func_str = f"\nDesired function: {desired_function}" if desired_function else ""

    prompt = f"""You are a senior protein engineering scientist providing a concise report.

Sequence (first 40 aa shown): {sequence[:40]}{"..." if len(sequence) > 40 else ""}
Mutations introduced: {mut_str}{func_str}

Computed biophysical properties:
{props_str}

Write a 3–5 sentence scientific explanation of:
1. What the mutations likely achieve.
2. Notable biophysical properties and their implications.
3. Recommendations for experimental validation.

Be factual, concise, and avoid overstatement. Do not claim specific binding affinities or 
activity levels that require experimental confirmation."""

    try:
        return _generate(prompt, temperature=0.4)
    except Exception as exc:
        logger.warning("Gemini explanation failed: %s", exc)
        return (
            f"Designed sequence with mutations: {mut_str}. "
            f"Biophysical properties computed. "
            f"Gemini explanation unavailable: {exc}"
        )
