"""
Pydantic schemas for request validation and response serialization.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")


def _validate_aa_sequence(v: str) -> str:
    cleaned = v.strip().upper().replace(" ", "").replace("\n", "")
    invalid = set(cleaned) - VALID_AA
    if invalid:
        raise ValueError(
            f"Sequence contains invalid amino acid characters: {invalid}"
        )
    if len(cleaned) < 4:
        raise ValueError("Sequence must be at least 4 amino acids long.")
    return cleaned


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class DesignRequest(BaseModel):
    sequence: str | None = Field(
        default=None,
        description="Raw amino acid sequence (single-letter code).",
        example="EVQLVESGGGLVQPGGSLRLSCAAS",
    )
    fasta_content: str | None = Field(
        default=None,
        description="Raw FASTA-formatted content (supports multi-FASTA).",
    )
    mutation_list: list[str] | None = Field(
        default=None,
        description="List of mutations in format 'A23V' (original_aa position new_aa).",
        example=["A23V", "K45R"],
    )
    target_antigen: str | None = Field(
        default=None,
        description="Target antigen sequence for binding design context.",
    )
    desired_function: str | None = Field(
        default=None,
        description="Free-text description of the desired protein function.",
        example="Design a thermostable antibody fragment binding to EGFR.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of candidate sequences to return.",
    )

    @field_validator("sequence", mode="before")
    @classmethod
    def validate_sequence(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _validate_aa_sequence(v)

    def model_post_init(self, __context: Any) -> None:
        if not self.sequence and not self.fasta_content and not self.mutation_list:
            raise ValueError(
                "At least one of 'sequence', 'fasta_content', or 'mutation_list' is required."
            )


class PredictRequest(BaseModel):
    sequence: str = Field(
        ...,
        description="Amino acid sequence to analyse.",
    )

    @field_validator("sequence", mode="before")
    @classmethod
    def validate_sequence(cls, v: str) -> str:
        return _validate_aa_sequence(v)


class BatchDesignRequest(BaseModel):
    requests: list[DesignRequest] = Field(
        ...,
        min_length=1,
        description="List of individual design requests.",
    )

    @field_validator("requests")
    @classmethod
    def check_batch_size(cls, v: list[DesignRequest]) -> list[DesignRequest]:
        if len(v) > 50:
            raise ValueError("Batch size cannot exceed 50 requests.")
        return v


class StructureRequest(BaseModel):
    sequence: str = Field(..., description="Amino acid sequence to fold.")
    job_id: str | None = Field(
        default=None,
        description="Optional job ID to store PDB alongside an existing job.",
    )

    @field_validator("sequence", mode="before")
    @classmethod
    def validate_sequence(cls, v: str) -> str:
        return _validate_aa_sequence(v)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class PropertyResult(BaseModel):
    instability_index: float
    isoelectric_point: float
    aromaticity: float
    molecular_weight: float
    gravy: float
    secondary_structure_fraction: dict[str, float]


class RankedSequence(BaseModel):
    sequence: str
    mutations_from_input: list[str]
    esm_score: float
    stability_proxy: float
    diversity_score: float
    heuristic_score: float
    rank: int


class ProteinResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    input_sequence: str | None = None
    designed_sequences: list[RankedSequence] = []
    properties: PropertyResult | None = None
    gemini_explanation: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StructureResponse(BaseModel):
    job_id: str | None = None
    sequence: str
    pdb_string: str
    mean_plddt: float
    min_plddt: float
    max_plddt: float
    confidence_note: str


class BatchDesignResponse(BaseModel):
    total: int
    results: list[ProteinResponse]


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
