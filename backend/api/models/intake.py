from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel

from api.models.enums import ScaffoldingDepth, sa_enum


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionIntake(SQLModel, table=True):
    """One learner's M0 intake and self-assessment, one row per session.

    Deliberately a separate table rather than columns on `Session`, for the
    same reason `FeedbackRecord` is separate: M0 is provisional, and dropping
    this table must not disturb the session flow that outlives it.

    The row is created by the diagnostic step and finished by the
    comprehension step, so the columns fall into two groups: those written at
    creation, and those that stay NULL until the flow completes.
    """

    __tablename__ = "session_intake"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Unique, not merely indexed: this carries both the 1:1 relationship and
    # the idempotency of the diagnostic step. A racing second submission is
    # rejected by the database rather than overwriting the learner's score.
    session_id: UUID = Field(foreign_key="session.id", unique=True)

    # Written at creation.
    diagnostic_answers: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    diagnostic_score: int
    # Derived from the diagnostic outcome, not reported by the frontend: the
    # primer has no endpoint, so this records what the frontend was told to
    # show, not what it observably showed.
    primer_shown: bool
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # NULL until the comprehension step finalizes the flow.
    comprehension_answer: str | None = Field(default=None)
    scaffolding_depth: ScaffoldingDepth | None = Field(
        default=None, sa_column=Column(sa_enum(ScaffoldingDepth), nullable=True)
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
