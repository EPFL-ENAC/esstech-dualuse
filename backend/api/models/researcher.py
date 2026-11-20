from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from api.models.base import timestamp_column, utc_now
from api.models.enums import (
    ContrastType,
    Domain,
    Form,
    Function,
    Gate,
    InclusionReason,
    MappingStatus,
    Pattern,
    sa_enum,
)


class TechnologyIntake(SQLModel, table=True):
    """One researcher's described technology and its Function/Form/Domain
    mapping, one row per session."""

    __tablename__ = "technology_intake"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id", unique=True)
    raw_description: str
    # NULL until mapped. Filled in progressively across clarification
    # rounds, not necessarily all at once.
    domain: Domain | None = Field(
        default=None, sa_column=Column(sa_enum(Domain), nullable=True)
    )
    functions: list[Function] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    forms: list[Form] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    mapping_status: MappingStatus = Field(
        default=MappingStatus.UNMAPPED,
        sa_column=Column(sa_enum(MappingStatus), nullable=False),
    )
    clarification_count: int = Field(default=0)
    # NULL until gate-and-posture, which requires mapping_status MAPPED.
    gate: Gate | None = Field(
        default=None, sa_column=Column(sa_enum(Gate), nullable=True)
    )
    # NULL until gate-and-posture -- the "who else could use it?" answer.
    posture_response: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(onupdate=utc_now),
    )


class ComparisonSet(SQLModel, table=True):
    """The set of cases matched to a session's technology intake, one row
    per session. `was_widened` records whether matching had to widen by
    domain."""

    __tablename__ = "comparison_set"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id", unique=True)
    # The Function set actually used for this matching run -- may be a
    # superset of TechnologyIntake.functions when was_widened is true.
    functions: list[Function] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    was_widened: bool = Field(default=False)
    case_count: int
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )


class ComparisonSetCase(SQLModel, table=True):
    """One case included in a comparison set, with why it was included."""

    __tablename__ = "comparison_set_case"
    __table_args__ = (
        UniqueConstraint(
            "comparison_set_id", "case_id", name="uq_comparison_set_case_set_case"
        ),
        UniqueConstraint(
            "comparison_set_id",
            "sequence_no",
            name="uq_comparison_set_case_set_sequence",
        ),
        # Created by migration f527b60e072a. Declared here so autogenerate
        # does not propose dropping it; changing InclusionReason needs a
        # migration that recreates it.
        CheckConstraint(
            "inclusion_reason IN ("
            + ", ".join(f"'{reason.value}'" for reason in InclusionReason)
            + ")",
            name="ck_comparison_set_case_inclusion_reason",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    comparison_set_id: UUID = Field(foreign_key="comparison_set.id", index=True)
    case_id: UUID = Field(foreign_key="case.id", index=True)
    inclusion_reason: InclusionReason = Field(
        sa_column=Column(sa_enum(InclusionReason), nullable=False)
    )
    # 0-indexed position in the relevance order computed at build time
    # (unlike CaseEncounter/Commitment's 1-indexed sequence_no).
    sequence_no: int


class ResearcherPrediction(SQLModel, table=True):
    """One ranked pattern in a researcher's dual-use risk prediction."""

    __tablename__ = "researcher_prediction"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "rank", name="uq_researcher_prediction_session_rank"
        ),
        UniqueConstraint(
            "session_id",
            "pattern",
            name="uq_researcher_prediction_session_pattern",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id", index=True)
    rank: int
    pattern: Pattern = Field(sa_column=Column(sa_enum(Pattern), nullable=False))
    submitted_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )


class SetContrastEntry(SQLModel, table=True):
    """The post-reveal contrast reflection for a session's comparison set.

    Scoped to the set as a whole: contrast_type reflects whether any case
    in the set has a linked counter-case, and the WHO question is about
    the pattern across the set, hence no counter_case_id.
    """

    __tablename__ = "set_contrast_entry"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Unique: makes set-contrast submission idempotent at the data level.
    session_id: UUID = Field(foreign_key="session.id", unique=True)
    contrast_type: ContrastType = Field(
        sa_column=Column(sa_enum(ContrastType), nullable=False)
    )
    # NULL exactly when contrast_type is OPEN_AREA.
    learner_response: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
