from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel

from api.models.enums import (
    CaseStatus,
    CaseType,
    Domain,
    Form,
    Function,
    Gate,
    Pattern,
    sa_enum,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Case(SQLModel, table=True):
    """A curated case study presented to a learner."""

    __tablename__ = "case"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    area: str = Field(index=True)
    case_type: CaseType = Field(sa_column=Column(sa_enum(CaseType), nullable=False))
    status: CaseStatus = Field(
        default=CaseStatus.DRAFT,
        sa_column=Column(sa_enum(CaseStatus), nullable=False, index=True),
    )
    narrative_until_crossroads: str
    full_narrative: str
    main_path_pattern: Pattern = Field(
        sa_column=Column(sa_enum(Pattern), nullable=False)
    )
    main_path_gate: Gate = Field(sa_column=Column(sa_enum(Gate), nullable=False))
    # Free-text citations, displayed as-is and never filtered on, so a JSON list
    # is enough -- unlike tagged patterns/gates below, this needs no join table.
    source_references: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    # Structured technology domain, used only by Researcher-route matching.
    # Distinct from `area` above on purpose: `area` is free-text editorial
    # copy already shown in the Student UI via CaseCandidate (verified
    # end-to-end in Sprint 2, do not touch it), while `domain` is a fixed
    # enum a case is tagged with for Function/Form/Domain comparison-set
    # matching. This is not duplication to clean up later.
    domain: Domain = Field(sa_column=Column(sa_enum(Domain), nullable=False))
    # Never filtered or joined on, same reasoning as source_references above
    # -- a JSON list is enough, no join table needed.
    forms: list[Form] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=_utc_now),
    )


class CaseTaggedPattern(SQLModel, table=True):
    """One pattern tagged on a case. A case can carry several patterns."""

    __tablename__ = "case_tagged_pattern"

    case_id: UUID = Field(foreign_key="case.id", primary_key=True)
    pattern: Pattern = Field(
        sa_column=Column(sa_enum(Pattern), primary_key=True, nullable=False)
    )


class CaseTaggedGate(SQLModel, table=True):
    """One decision gate tagged on a case. A case can carry several gates."""

    __tablename__ = "case_tagged_gate"

    case_id: UUID = Field(foreign_key="case.id", primary_key=True)
    gate: Gate = Field(
        sa_column=Column(sa_enum(Gate), primary_key=True, nullable=False)
    )


class CaseTaggedFunction(SQLModel, table=True):
    """One function tagged on a case. A case can carry several functions."""

    __tablename__ = "case_tagged_function"

    case_id: UUID = Field(foreign_key="case.id", primary_key=True)
    function: Function = Field(
        sa_column=Column(sa_enum(Function), primary_key=True, nullable=False)
    )


class CounterCaseLink(SQLModel, table=True):
    """Links a harm case to the counter-case that contrasts with it."""

    __tablename__ = "counter_case_link"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    harm_case_id: UUID = Field(foreign_key="case.id", index=True)
    # Unique: assumes one counter-case contrasts exactly one harm case. Revisit
    # once the real case corpus shows whether a counter-case is ever reused
    # across multiple harm cases.
    counter_case_id: UUID = Field(foreign_key="case.id", unique=True)
    responsibility_posture_contrast: str
    gate_lever: Gate = Field(sa_column=Column(sa_enum(Gate), nullable=False))
