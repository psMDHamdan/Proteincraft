"""
FASTA parsing and amino acid sequence validation utilities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

VALID_AA_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY]+$")


@dataclass
class FastaRecord:
    header: str
    sequence: str


def parse_fasta(content: str) -> list[FastaRecord]:
    """
    Parse a FASTA-formatted string into a list of FastaRecord objects.

    Supports multi-FASTA content.  Blank lines and Windows line endings
    are handled transparently.

    Args:
        content: Raw FASTA string (may start with '>' or not).

    Returns:
        List of FastaRecord instances.

    Raises:
        ValueError: If the content contains no valid FASTA records.
    """
    records: list[FastaRecord] = []
    current_header: str | None = None
    current_seq_parts: list[str] = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_header is not None:
                seq = "".join(current_seq_parts).upper()
                records.append(FastaRecord(header=current_header, sequence=seq))
            current_header = line[1:].strip()
            current_seq_parts = []
        else:
            current_seq_parts.append(line)

    # Flush last record
    if current_header is not None:
        seq = "".join(current_seq_parts).upper()
        records.append(FastaRecord(header=current_header, sequence=seq))

    if not records:
        raise ValueError(
            "No valid FASTA records found. "
            "Ensure the content starts with '>' headers."
        )

    return records


def validate_sequence(sequence: str) -> tuple[bool, str | None]:
    """
    Validate an amino acid sequence.

    Returns:
        (True, None) if valid.
        (False, error_message) if invalid.
    """
    cleaned = sequence.strip().upper().replace(" ", "").replace("\n", "")
    if len(cleaned) < 4:
        return False, "Sequence too short (minimum 4 amino acids)."
    if not VALID_AA_RE.match(cleaned):
        invalid = set(cleaned) - set("ACDEFGHIKLMNPQRSTVWY")
        return False, f"Invalid amino acid characters: {sorted(invalid)}"
    return True, None


def apply_mutations(sequence: str, mutations: list[str]) -> str:
    """
    Apply a list of mutations to a sequence.

    Mutation format: 'A23V'  — original_aa, 1-based position, new_aa.

    Args:
        sequence: Wild-type amino acid sequence.
        mutations: List of mutation strings.

    Returns:
        Mutated sequence.

    Raises:
        ValueError: On invalid mutation format or position mismatch.
    """
    mutation_re = re.compile(r"^([A-Z])(\d+)([A-Z])$")
    seq_list = list(sequence.upper())

    for mut in mutations:
        m = mutation_re.match(mut.strip().upper())
        if not m:
            raise ValueError(
                f"Invalid mutation format '{mut}'. Expected format: 'A23V'."
            )
        orig, pos_str, new = m.group(1), m.group(2), m.group(3)
        pos = int(pos_str) - 1  # Convert to 0-based index

        if pos < 0 or pos >= len(seq_list):
            raise ValueError(
                f"Mutation position {pos + 1} is out of range for sequence "
                f"of length {len(seq_list)}."
            )
        if seq_list[pos] != orig:
            raise ValueError(
                f"Mutation {mut}: expected '{orig}' at position {pos + 1}, "
                f"found '{seq_list[pos]}'."
            )
        seq_list[pos] = new

    return "".join(seq_list)
