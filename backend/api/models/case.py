from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from api.models.base import timestamp_column, utc_now
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
    # Free-text citations, never filtered on: a JSON list, not a join table.
    source_references: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    # Not a duplicate of `area`: `area` is free-text editorial copy shown in
    # the Student UI; `domain` is the fixed taxonomy value used for
    # Researcher-route comparison-set matching.
    domain: Domain = Field(sa_column=Column(sa_enum(Domain), nullable=False))
    # Never filtered on: a JSON list, not a join table.
    forms: list[Form] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(onupdate=utc_now),
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
