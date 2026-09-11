from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from api.models.enums import ContrastType, sa_enum


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContrastEntry(SQLModel, table=True):
    """The post-reveal reflection for one encounter: a twin counter-case
    response, or an open-area acknowledgement when none exists."""

    __tablename__ = "contrast_entry"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Unique, not merely indexed: this is what makes contrast submission
    # idempotent at the data level, the same way FeedbackRecord.case_encounter_id
    # guards reveal.
    case_encounter_id: UUID = Field(foreign_key="case_encounter.id", unique=True)
    contrast_type: ContrastType = Field(
        sa_column=Column(sa_enum(ContrastType), nullable=False)
    )
    # NULL exactly when contrast_type is OPEN_AREA.
    counter_case_id: UUID | None = Field(
        default=None, foreign_key="case.id", index=True
    )
    # NULL for open_area. For twin_counter_case this is always non-empty by the
    # time a row exists -- enforced in the service layer, not by a NOT NULL
    # column, since the same column must stay nullable for the other branch.
    learner_response: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
