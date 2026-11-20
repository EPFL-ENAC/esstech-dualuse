from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import (
    Case,
    CaseTaggedFunction,
    CaseTaggedPattern,
    ComparisonSet,
    ComparisonSetCase,
    ResearcherPrediction,
    SetContrastEntry,
    TechnologyIntake,
)
from api.models.enums import (
    ContrastType,
    Domain,
    Form,
    Function,
    Gate,
    InclusionReason,
    MappingStatus,
    Pattern,
)
from api.services.cases import offerable_cases
from api.services.contrast import (
    CounterCaseResponse,
    counter_case_response,
    find_counter_case_link,
    resolve_contrast,
)
from api.services.errors import ConflictError, NotFoundError, ValidationError
from api.services.persistence import insert_once
from api.services.researcher_queries import (
    MAX_TAG_ATTEMPTS,
    attempts_remaining,
    comparison_case_ids,
    find_comparison_set,
    find_predictions,
    find_set_contrast_entry,
    find_technology_intake,
)

# Below this many Function-matched cases, widen by Domain. Not configurable:
# a fixed corpus-size floor for a comparison to be meaningful at all.
MIN_COMPARISON_SET_SIZE = 5


class ComparisonSetCaseSummary(BaseModel):
    """One case in a comparison set, in relevance order."""

    case_id: UUID
    title: str
    domain: Domain


class ComparisonSetResult(BaseModel):
    """The cases matched to a session's technology intake."""

    cases: list[ComparisonSetCaseSummary]
    was_widened: bool
    case_count: int


class PatternDistribution(BaseModel):
    """How tagged patterns distribute across a set of cases.

    dominant is None exactly when no matched case carries a tagged pattern. This is a real
    branch (Fase 6: "Any pattern activated? No -> Low-activation report"),
    not a hypothetical one -- callers must handle it.
    """

    dominant: Pattern | None
    secondary: list[Pattern]


class GateAndPostureSubmission(BaseModel):
    """Request body for filling a mapped session's gate and posture fields."""

    gate: Gate
    posture_response: str


class GateAndPostureResult(BaseModel):
    """The gate and posture fields just written to a session's technology intake."""

    gate: Gate
    posture_response: str


class SetContrastSubmission(BaseModel):
    """Request body for the session-level post-reveal contrast reflection."""

    learner_response: str | None = None


class SetContrastResponse(BaseModel):
    """The stored set-level contrast entry, whichever branch produced it."""

    set_contrast_entry_id: UUID
    contrast_type: ContrastType
    learner_response: str | None
    created_at: datetime


class PredictionEntry(BaseModel):
    """One ranked pattern in a submitted prediction set."""

    rank: int
    pattern: Pattern


class PredictionSubmission(BaseModel):
    """Request body for a session's one-shot dual-use risk prediction."""

    predictions: list[PredictionEntry]


class PredictionSubmissionResult(BaseModel):
    """A session's one-shot dual-use risk prediction, once stored."""

    predictions: list[PredictionEntry]


class TechnologyIntakeCreate(BaseModel):
    """Request body for starting a session's technology intake."""

    raw_description: str


class TechnologyIntakeCreated(BaseModel):
    """A newly started technology intake, before any mapping."""

    id: UUID
    session_id: UUID
    raw_description: str
    mapping_status: MappingStatus
    created_at: datetime


class TagSubmission(BaseModel):
    """Request body for one /tag attempt."""

    domain: Domain | None = None
    functions: list[Function] = Field(default_factory=list)
    forms: list[Form] = Field(default_factory=list)


class TagResult(BaseModel):
    """The outcome of one /tag attempt: current mapping state, and
    whether another attempt remains."""

    domain: Domain | None
    functions: list[Function]
    forms: list[Form]
    mapping_status: MappingStatus
    attempts_used: int
    attempts_remaining: int


class TechnologyIntakeState(BaseModel):
    """The full stored technology intake, for recovering an interrupted flow."""

    session_id: UUID
    raw_description: str
    domain: Domain | None
    functions: list[Function]
    forms: list[Form]
    mapping_status: MappingStatus
    attempts_used: int
    attempts_remaining: int
    gate: Gate | None
    posture_response: str | None
    created_at: datetime


class RevealComparison(BaseModel):
    """A session's prediction compared against its comparison set's tagged
    pattern distribution. Structured facts, not a verdict."""

    dominant_pattern: Pattern | None
    secondary_patterns: list[Pattern]
    predictions: list[PredictionEntry]
    top_prediction_is_dominant: bool
    predictions_in_secondary: list[Pattern]
    predictions_not_activated: list[Pattern]


def check_mapping_status(
    domain: Domain | None,
    functions: list[Function] | None,
    forms: list[Form] | None,
) -> MappingStatus:
    """Derive a MappingStatus from the three Function/Form/Domain facets.
    A null or empty facet counts as absent."""

    present = (domain is not None, bool(functions), bool(forms))
    count = sum(present)
    if count == 3:
        return MappingStatus.MAPPED
    if count == 0:
        return MappingStatus.UNMAPPED
    return MappingStatus.PARTIAL


async def create_technology_intake(
    session: AsyncSession,
    *,
    session_id: UUID,
    raw_description: str,
) -> TechnologyIntakeCreated:
    """Start a session's technology intake from its free-text description.

    A repeated call returns the stored intake unchanged, so a retried POST
    is safe when the first response was lost.
    """

    record = await find_technology_intake(session, session_id=session_id)
    if record is None:
        record, created = await insert_once(
            session,
            TechnologyIntake(
                session_id=session_id,
                raw_description=raw_description,
                mapping_status=MappingStatus.UNMAPPED,
            ),
            lambda: find_technology_intake(session, session_id=session_id),
        )
        if created:
            await session.commit()

    return TechnologyIntakeCreated(
        id=record.id,
        session_id=record.session_id,
        raw_description=record.raw_description,
        mapping_status=record.mapping_status,
        created_at=record.created_at,
    )


async def submit_tag(
    session: AsyncSession,
    *,
    session_id: UUID,
    domain: Domain | None,
    functions: list[Function],
    forms: list[Form],
) -> TagResult:
    """Record one attempt at tagging a session's technology intake.

    Exhausting the attempt budget is a normal terminal outcome (the
    boundary exit), so the call that does it still succeeds.
    """

    intake = await find_technology_intake(session, session_id=session_id)
    if intake is None:
        raise ConflictError("Session has no technology intake")
    if intake.mapping_status == MappingStatus.MAPPED:
        raise ConflictError(
            "Technology is already mapped; no more tagging attempts allowed"
        )
    if intake.clarification_count >= MAX_TAG_ATTEMPTS:
        raise ConflictError("No tagging attempts remain for this session")

    intake.domain = domain
    intake.functions = functions
    intake.forms = forms
    intake.mapping_status = check_mapping_status(domain, functions, forms)
    if intake.mapping_status != MappingStatus.MAPPED:
        intake.clarification_count += 1
    session.add(intake)
    await session.commit()

    return TagResult(
        domain=intake.domain,
        functions=intake.functions or [],
        forms=intake.forms or [],
        mapping_status=intake.mapping_status,
        attempts_used=intake.clarification_count,
        attempts_remaining=attempts_remaining(intake),
    )


async def get_technology_intake(
    session: AsyncSession, *, session_id: UUID
) -> TechnologyIntakeState:
    """Return the stored technology intake, so a reloaded page can resume
    mid-flow."""

    intake = await find_technology_intake(session, session_id=session_id)
    if intake is None:
        raise NotFoundError("Technology intake not found")

    return TechnologyIntakeState(
        session_id=intake.session_id,
        raw_description=intake.raw_description,
        domain=intake.domain,
        functions=intake.functions or [],
        forms=intake.forms or [],
        mapping_status=intake.mapping_status,
        attempts_used=intake.clarification_count,
        attempts_remaining=attempts_remaining(intake),
        gate=intake.gate,
        posture_response=intake.posture_response,
        created_at=intake.created_at,
    )


async def set_gate_and_posture(
    session: AsyncSession,
    *,
    session_id: UUID,
    gate: Gate,
    posture_response: str,
) -> GateAndPostureResult:
    """Fill a mapped session's gate and posture-response fields.

    One-shot: the posture question captures a first genuine reflection at
    the moment the researcher has just confirmed their technology, so it
    is never overwritten.
    """

    intake = await find_technology_intake(session, session_id=session_id)
    if intake is None:
        raise ConflictError("Session has no technology intake")
    if intake.mapping_status != MappingStatus.MAPPED:
        raise ConflictError("Technology must be fully mapped before gate and posture")
    if intake.gate is not None or intake.posture_response is not None:
        raise ConflictError("Gate and posture have already been submitted")

    intake.gate = gate
    intake.posture_response = posture_response
    session.add(intake)
    await session.commit()

    return GateAndPostureResult(gate=gate, posture_response=posture_response)


async def submit_prediction(
    session: AsyncSession,
    *,
    session_id: UUID,
    predictions: list[PredictionEntry],
) -> PredictionSubmissionResult:
    """Store a session's one-shot dual-use risk prediction.

    Ranks must be consecutive from 1; /reveal relies on rank 1 existing.
    """

    if await find_predictions(session, session_id=session_id):
        raise ConflictError("Session already has a submitted prediction")

    if len(predictions) not in (2, 3):
        raise ValidationError("A prediction must have exactly 2 or 3 ranked patterns")

    ranks = [entry.rank for entry in predictions]
    expected_ranks = set(range(1, len(predictions) + 1))
    if set(ranks) != expected_ranks:
        raise ValidationError(
            "Ranks must be exactly {1, 2} or {1, 2, 3} -- consecutive, "
            "starting at 1, with no gaps or duplicates"
        )

    patterns = [entry.pattern for entry in predictions]
    if len(set(patterns)) != len(patterns):
        raise ValidationError("The same pattern cannot be predicted twice")

    for entry in predictions:
        session.add(
            ResearcherPrediction(
                session_id=session_id,
                rank=entry.rank,
                pattern=entry.pattern,
            )
        )
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("Session already has a submitted prediction") from exc

    return PredictionSubmissionResult(predictions=predictions)


async def _respond(
    session: AsyncSession, comparison_set: ComparisonSet
) -> ComparisonSetResult:
    rows = (
        await session.exec(
            select(ComparisonSetCase, Case)
            .join(Case, col(Case.id) == col(ComparisonSetCase.case_id))
            .where(ComparisonSetCase.comparison_set_id == comparison_set.id)
            .order_by(col(ComparisonSetCase.sequence_no))
        )
    ).all()
    return ComparisonSetResult(
        cases=[
            ComparisonSetCaseSummary(
                case_id=membership.case_id, title=case.title, domain=case.domain
            )
            for membership, case in rows
        ],
        was_widened=comparison_set.was_widened,
        case_count=comparison_set.case_count,
    )


async def _find_function_matched_cases(
    session: AsyncSession, *, functions: list[Function]
) -> list[UUID]:
    """Published HARM cases sharing >=1 Function with `functions`, most
    shared functions first."""

    if not functions:
        return []

    rows = (
        await session.exec(
            select(CaseTaggedFunction.case_id, func.count())
            .join(Case, col(Case.id) == col(CaseTaggedFunction.case_id))
            .where(
                col(CaseTaggedFunction.function).in_(functions),
                *offerable_cases(),
            )
            .group_by(col(CaseTaggedFunction.case_id))
        )
    ).all()

    ordered = sorted(rows, key=lambda pair: (-pair[1], pair[0]))
    return [case_id for case_id, _ in ordered]


async def _find_domain_widen_candidates(
    session: AsyncSession, *, domain: Domain, exclude_case_ids: set[UUID]
) -> list[UUID]:
    """Published HARM cases in `domain`, excluding ones already matched."""

    case_ids = (
        await session.exec(
            select(Case.id)
            .where(Case.domain == domain, *offerable_cases())
            .order_by(col(Case.id))
        )
    ).all()
    return [case_id for case_id in case_ids if case_id not in exclude_case_ids]


async def build_comparison_set(
    session: AsyncSession, *, session_id: UUID
) -> ComparisonSetResult:
    """Match a session's technology intake against the case corpus.

    An existing ComparisonSet is returned unchanged, never recomputed.
    """

    existing = await find_comparison_set(session, session_id=session_id)
    if existing is not None:
        return await _respond(session, existing)

    intake = await find_technology_intake(session, session_id=session_id)
    if intake is None:
        raise ConflictError("Session has no technology intake to match")

    functions = intake.functions or []
    function_matched_ids = await _find_function_matched_cases(
        session, functions=functions
    )

    was_widened = False
    widened_ids: list[UUID] = []
    if (
        len(function_matched_ids) < MIN_COMPARISON_SET_SIZE
        and intake.domain is not None
    ):
        candidates = await _find_domain_widen_candidates(
            session,
            domain=intake.domain,
            exclude_case_ids=set(function_matched_ids),
        )
        needed = MIN_COMPARISON_SET_SIZE - len(function_matched_ids)
        widened_ids = candidates[:needed]
        was_widened = len(widened_ids) > 0

    case_count = len(function_matched_ids) + len(widened_ids)
    comparison_set, created = await insert_once(
        session,
        ComparisonSet(
            session_id=session_id,
            functions=functions,
            was_widened=was_widened,
            case_count=case_count,
        ),
        lambda: find_comparison_set(session, session_id=session_id),
    )
    if not created:
        return await _respond(session, comparison_set)

    for sequence_no, case_id in enumerate(function_matched_ids):
        session.add(
            ComparisonSetCase(
                comparison_set_id=comparison_set.id,
                case_id=case_id,
                inclusion_reason=InclusionReason.SHARED_FUNCTION,
                sequence_no=sequence_no,
            )
        )
    for sequence_no, case_id in enumerate(widened_ids, start=len(function_matched_ids)):
        session.add(
            ComparisonSetCase(
                comparison_set_id=comparison_set.id,
                case_id=case_id,
                inclusion_reason=InclusionReason.WIDENED_BY_DOMAIN,
                sequence_no=sequence_no,
            )
        )
    await session.commit()

    return await _respond(session, comparison_set)


async def get_pattern_distribution(
    session: AsyncSession, *, case_ids: list[UUID]
) -> PatternDistribution:
    """Tally tagged-pattern frequency across `case_ids`. Ties are broken
    alphabetically by Pattern value."""

    if not case_ids:
        return PatternDistribution(dominant=None, secondary=[])

    rows = (
        await session.exec(
            select(CaseTaggedPattern.pattern, func.count())
            .where(col(CaseTaggedPattern.case_id).in_(case_ids))
            .group_by(col(CaseTaggedPattern.pattern))
        )
    ).all()
    # ty stub gap: rows of a multi-column select over an sa_enum column are
    # not inferred as Pattern, though that is the runtime value.
    pattern_counts: dict[Pattern, int] = {pattern: count for pattern, count in rows}  # type: ignore

    # No tagged pattern on any matched case: Fase 6's low-activation report.
    if not pattern_counts:
        return PatternDistribution(dominant=None, secondary=[])

    dominant = min(
        pattern_counts, key=lambda pattern: (-pattern_counts[pattern], pattern.value)
    )
    secondary = sorted(
        (pattern for pattern in pattern_counts if pattern != dominant),
        key=lambda pattern: (-pattern_counts[pattern], pattern.value),
    )

    return PatternDistribution(dominant=dominant, secondary=secondary)


async def reveal_prediction_comparison(
    session: AsyncSession, *, session_id: UUID
) -> RevealComparison:
    """Compare a session's submitted prediction against its comparison
    set's tagged-pattern distribution."""

    case_ids = await comparison_case_ids(session, session_id=session_id)
    distribution = await get_pattern_distribution(session, case_ids=case_ids)

    prediction_rows = await find_predictions(session, session_id=session_id)
    if not prediction_rows:
        raise ConflictError("Session has no submitted prediction to reveal against")

    predictions = [
        PredictionEntry(rank=row.rank, pattern=row.pattern) for row in prediction_rows
    ]

    top_prediction = predictions[0]
    top_prediction_is_dominant = (
        distribution.dominant is not None
        and top_prediction.pattern == distribution.dominant
    )
    predictions_in_secondary = [
        entry.pattern
        for entry in predictions
        if entry.pattern in distribution.secondary
    ]
    activated = set(distribution.secondary)
    if distribution.dominant is not None:
        activated.add(distribution.dominant)
    predictions_not_activated = [
        entry.pattern for entry in predictions if entry.pattern not in activated
    ]

    return RevealComparison(
        dominant_pattern=distribution.dominant,
        secondary_patterns=distribution.secondary,
        predictions=predictions,
        top_prediction_is_dominant=top_prediction_is_dominant,
        predictions_in_secondary=predictions_in_secondary,
        predictions_not_activated=predictions_not_activated,
    )


async def look_up_set_counter_case(
    session: AsyncSession, *, session_id: UUID
) -> CounterCaseResponse:
    case_ids = await comparison_case_ids(session, session_id=session_id)
    return counter_case_response(
        await find_counter_case_link(session, case_ids=case_ids)
    )


def _respond_set_contrast(entry: SetContrastEntry) -> SetContrastResponse:
    return SetContrastResponse(
        set_contrast_entry_id=entry.id,
        contrast_type=entry.contrast_type,
        learner_response=entry.learner_response,
        created_at=entry.created_at,
    )


async def submit_set_contrast(
    session: AsyncSession,
    *,
    session_id: UUID,
    learner_response: str | None,
) -> SetContrastResponse:
    """Record the session's set-level contrast reflection, computing it only
    the first time. The branch depends on whether any case in the comparison
    set has a counter-case."""

    existing = await find_set_contrast_entry(session, session_id=session_id)
    if existing is not None:
        return _respond_set_contrast(existing)

    case_ids = await comparison_case_ids(session, session_id=session_id)

    link = await find_counter_case_link(session, case_ids=case_ids)
    contrast_type, learner_response = resolve_contrast(link, learner_response)

    record, created = await insert_once(
        session,
        SetContrastEntry(
            session_id=session_id,
            contrast_type=contrast_type,
            learner_response=learner_response,
        ),
        lambda: find_set_contrast_entry(session, session_id=session_id),
    )
    if created:
        await session.commit()

    return _respond_set_contrast(record)
