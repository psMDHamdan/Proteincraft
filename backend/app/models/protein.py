"""
ORM model for protein design jobs.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProteinJob(Base):
    __tablename__ = "protein_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Input
    input_sequence: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_fasta_header: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mutation_list: Mapped[list | None] = mapped_column(JSON, nullable=True)
    target_antigen: Mapped[str | None] = mapped_column(Text, nullable=True)
    desired_function: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(32), default="pending", nullable=False, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Outputs
    designed_sequences: Mapped[list | None] = mapped_column(JSON, nullable=True)
    properties_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scores_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pdb_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    gemini_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ProteinJob id={self.id} status={self.status}>"
