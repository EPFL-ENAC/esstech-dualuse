from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from api.models.base import timestamp_column, utc_now
from api.models.enums import ScaffoldingDepth, sa_enum


class SessionIntake(SQLModel, table=True):
    """One learner's M0 intake and self-assessment, one row per session.

    A separate table rather than columns on `Session`: M0 is provisional,
    and dropping this table must not disturb the session flow.
    """

    __tablename__ = "session_intake"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Unique: a racing second diagnostic submission is rejected by the
    # database rather than overwriting the learner's score.
    session_id: UUID = Field(foreign_key="session.id", unique=True)

    # Written at creation.
    diagnostic_answers: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    diagnostic_score: int
    # What the frontend was told to show, not what it observably showed:
    # the primer has no endpoint.
    primer_shown: bool
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )

    # NULL until the comprehension step finalizes the flow.
    comprehension_answer: str | None = Field(default=None)
    scaffolding_depth: ScaffoldingDepth | None = Field(
        default=None, sa_column=Column(sa_enum(ScaffoldingDepth), nullable=True)
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=timestamp_column(nullable=True)
    )
