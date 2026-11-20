from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlmodel import Field, SQLModel

from api.models.base import timestamp_column, utc_now
from api.models.enums import MatchResult, sa_enum


class FeedbackRecord(SQLModel, table=True):
    """The computed reveal for one encounter, kept stable once written."""

    __tablename__ = "feedback_record"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Unique: a racing second reveal is rejected by the database rather than
    # producing a second, divergent verdict for the same encounter.
    case_encounter_id: UUID = Field(foreign_key="case_encounter.id", unique=True)
    commitment_id: UUID = Field(foreign_key="commitment.id", index=True)
    match_result: MatchResult = Field(
        sa_column=Column(sa_enum(MatchResult), nullable=False)
    )
    revealed_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
