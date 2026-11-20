from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from api.models.base import timestamp_column, utc_now
from api.models.enums import Gate, Pattern, SessionMode, SessionRoute, sa_enum


class Session(SQLModel, table=True):
    """One run through the tool by one learner."""

    __tablename__ = "session"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    route: SessionRoute = Field(sa_column=Column(sa_enum(SessionRoute), nullable=False))
    mode: SessionMode = Field(sa_column=Column(sa_enum(SessionMode), nullable=False))
    # Not a foreign key to LearningIdentity: get_current_learner() also
    # yields dev-cookie learner_ids that have no identity row.
    learner_id: UUID = Field(index=True)
    started_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=timestamp_column(nullable=True)
    )


MAX_ENCOUNTERS_PER_SESSION = 3


class CaseEncounter(SQLModel, table=True):
    """One case worked through inside a session."""

    __tablename__ = "case_encounter"
    __table_args__ = (
        CheckConstraint(
            f"sequence_no >= 1 AND sequence_no <= {MAX_ENCOUNTERS_PER_SESSION}",
            name="ck_case_encounter_sequence_no_range",
        ),
        UniqueConstraint(
            "session_id", "sequence_no", name="uq_case_encounter_session_sequence"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id", index=True)
    case_id: UUID = Field(foreign_key="case.id", index=True)
    sequence_no: int
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
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
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
    pattern: Pattern = Field(sa_column=Column(sa_enum(Pattern), nullable=False))
    gate: Gate = Field(sa_column=Column(sa_enum(Gate), nullable=False))
    # Free-form Q&A that led to this commitment; a blob because no
    # FramingQuestion entity exists.
    framing_answers: dict = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
