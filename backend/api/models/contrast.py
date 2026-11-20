from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlmodel import Field, SQLModel

from api.models.base import timestamp_column, utc_now
from api.models.enums import ContrastType, sa_enum


class ContrastEntry(SQLModel, table=True):
    """The post-reveal reflection for one encounter: a twin counter-case
    response, or an open-area acknowledgement when none exists."""

    __tablename__ = "contrast_entry"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Unique: makes contrast submission idempotent at the data level.
    case_encounter_id: UUID = Field(foreign_key="case_encounter.id", unique=True)
    contrast_type: ContrastType = Field(
        sa_column=Column(sa_enum(ContrastType), nullable=False)
    )
    # NULL exactly when contrast_type is OPEN_AREA.
    counter_case_id: UUID | None = Field(
        default=None, foreign_key="case.id", index=True
    )
    # NULL for open_area; non-empty for twin_counter_case (enforced in the
    # service layer, since the column must stay nullable for open_area).
    learner_response: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
