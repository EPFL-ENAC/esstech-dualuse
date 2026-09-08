from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from api.models.enums import Gate, Pattern, SessionMode, SessionRoute, sa_enum


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Session(SQLModel, table=True):
    """One run through the tool by one learner."""

    __tablename__ = "session"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    route: SessionRoute = Field(sa_column=Column(sa_enum(SessionRoute), nullable=False))
    mode: SessionMode = Field(sa_column=Column(sa_enum(SessionMode), nullable=False))
    # Not a foreign key: there is no User/LearningIdentity table yet. This is
    # the seam get_current_learner() feeds -- swapping in real identity later
    # only means changing what populates this column, not its shape.
    learner_id: UUID = Field(index=True)
    started_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class CaseEncounter(SQLModel, table=True):
    """One case worked through inside a session. A session holds up to 3."""

    __tablename__ = "case_encounter"
    __table_args__ = (
        CheckConstraint(
            "sequence_no >= 1 AND sequence_no <= 3",
            name="ck_case_encounter_sequence_no_range",
        ),
        UniqueConstraint(
            "session_id", "sequence_no", name="uq_case_encounter_session_sequence"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id", index=True)
    case_id: UUID = Field(foreign_key="case.id", index=True)
    # Bounded to 1..3 by the check constraint above and unique per session, so
    # a session can never accumulate more than 3 rows -- enforced by the
    # database itself, not by a check-then-insert in application code.
    sequence_no: int
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Commitment(SQLModel, table=True):
    """A learner's committed interpretation for one encounter.

    Multiple commitments per encounter are expected, not exceptional: group
    mode lets a learner re-vote after seeing the group distribution, and both
    the original and the revised commitment must survive as separate rows.
    """

    __tablename__ = "commitment"
    __table_args__ = (
        CheckConstraint("sequence_no >= 1", name="ck_commitment_sequence_no_positive"),
        UniqueConstraint(
            "case_encounter_id",
            "sequence_no",
            name="uq_commitment_encounter_sequence",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    case_encounter_id: UUID = Field(foreign_key="case_encounter.id", index=True)
    sequence_no: int
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    pattern: Pattern = Field(sa_column=Column(sa_enum(Pattern), nullable=False))
    gate: Gate = Field(sa_column=Column(sa_enum(Gate), nullable=False))
    # Free-form Q&A that led to this commitment. No FramingQuestion entity
    # exists yet, so this stays a flexible blob rather than a rigid schema.
    framing_answers: dict = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
