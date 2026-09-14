from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from api.models.enums import (
    ContrastType,
    Domain,
    Form,
    Function,
    Gate,
    MappingStatus,
    Pattern,
    sa_enum,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TechnologyIntake(SQLModel, table=True):
    """One researcher's described technology and its Function/Form/Domain
    mapping, one row per session.

    Mirrors SessionIntake's 1:1-per-session shape: `session_id` is unique,
    not merely indexed, for the same reason -- there is exactly one
    technology intake per Researcher-route session.
    """

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
    # Defaults to UNMAPPED: the row is created incomplete, at the first
    # free-text submission, before domain/functions/forms exist -- so
    # UNMAPPED must already be true at that exact moment, not left for the
    # service layer to remember to pass. Every later transition (as facets
    # get filled in) is still explicitly computed and passed at write time,
    # not derived automatically from the other columns.
    mapping_status: MappingStatus = Field(
        default=MappingStatus.UNMAPPED,
        sa_column=Column(sa_enum(MappingStatus), nullable=False),
    )
    clarification_count: int = Field(default=0)
    # NULL until gate-and-posture, filled only once mapping_status is
    # MAPPED -- same progressive-fill reasoning as domain/functions/forms
    # above, one step later in the flow.
    gate: Gate | None = Field(
        default=None, sa_column=Column(sa_enum(Gate), nullable=True)
    )
    # NULL until gate-and-posture -- the "who else could use it?" answer.
    posture_response: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=_utc_now),
    )


class ComparisonSet(SQLModel, table=True):
    """The set of cases matched to a session's technology intake, one row
    per session.

    Mirrors SessionIntake/TechnologyIntake's 1:1-per-session shape:
    `session_id` is unique, not merely indexed. Widening happens within one
    build operation, not as a separate later attempt -- `was_widened`
    records whether this session's one row required it, not a second row.
    """

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
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ComparisonSetCase(SQLModel, table=True):
    """One case included in a comparison set, with why it was included.

    Carries a synthetic id rather than a composite (comparison_set_id,
    case_id) primary key, the same way CounterCaseLink does and
    CaseTaggedPattern/CaseTaggedGate/CaseTaggedFunction don't: it holds an
    extra data column (inclusion_reason) beyond the pure link, not just
    the association itself.
    """

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
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    comparison_set_id: UUID = Field(foreign_key="comparison_set.id", index=True)
    case_id: UUID = Field(foreign_key="case.id", index=True)
    inclusion_reason: str
    # This case's position in the relevance order computed at build time
    # (shared-function count descending, then domain-widened, case id as
    # the tie-break) -- 0-indexed, not 1-indexed like CaseEncounter/
    # Commitment's sequence_no. Persisted so a later read can reconstruct
    # that order exactly, rather than only approximating it from
    # inclusion_reason/case_id.
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
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class SetContrastEntry(SQLModel, table=True):
    """The post-reveal contrast reflection for a session's comparison set.

    Mirrors Student's ContrastEntry (api/models/contrast.py), but scoped to
    the comparison set as a whole rather than one specific encounter's
    case: contrast_type reflects whether any case in the set has a linked
    counter-case, not one case's own link. No counter_case_id column --
    the WHO question here is about the pattern across the set, not one
    specific counter-case.
    """

    __tablename__ = "set_contrast_entry"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Unique, not merely indexed: 1:1 per session, same pattern as
    # TechnologyIntake/ComparisonSet, and the same idempotency guarantee
    # Student's ContrastEntry gets from case_encounter_id being unique.
    session_id: UUID = Field(foreign_key="session.id", unique=True)
    contrast_type: ContrastType = Field(
        sa_column=Column(sa_enum(ContrastType), nullable=False)
    )
    # NULL exactly when contrast_type is OPEN_AREA -- same rule as
    # Student's ContrastEntry.
    learner_response: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
