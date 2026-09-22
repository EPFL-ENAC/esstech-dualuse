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
    CounterCaseLink,
    ResearcherPrediction,
    SetContrastEntry,
    TechnologyIntake,
)
from api.models.enums import (
    CaseStatus,
    CaseType,
    ContrastType,
    Domain,
    Form,
    Function,
    Gate,
    InclusionReason,
    MappingStatus,
    Pattern,
    SessionRoute,
)
from api.services.errors import ConflictError, NotFoundError, ValidationError

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

    dominant is None exactly when pattern_counts is empty: no case_ids
    given, or none of the matched cases carry a tagged pattern. This is a
    real branch (Fase 6: "Any pattern activated? No -> Low-activation
    report"), not a hypothetical one -- callers must handle it.
    """

    dominant: Pattern | None
    secondary: list[Pattern]
    pattern_counts: dict[Pattern, int]


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


class SetCounterCaseInfo(BaseModel):
    """The counter-case fields shown before the set-level WHO reflection.

    Mirrors contrast.py's CounterCaseInfo exactly.
    """

    counter_case_id: UUID
    gate_lever: Gate
    responsibility_posture_contrast: str


class SetCounterCaseResponse(BaseModel):
    """Whether the session's comparison set has a linked counter-case.

    Mirrors contrast.py's CounterCaseResponse: needed so the frontend can
    show the twin-case content (or the open-area message) before asking
    for a reflection, rather than submitting blind and discovering which
    branch it was only from submit_set_contrast's own response.
    """

    has_counter_case: bool
    counter_case: SetCounterCaseInfo | None


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
    attempts_remaining: int


class TechnologyIntakeState(BaseModel):
    """The full stored technology intake, for recovering an interrupted flow.

    Mirrors Student's IntakeState (api/services/intake.py): everything a
    reloaded page needs to resume at the right step in one call, rather
    than reconstructing it from whichever individual POST responses
    happened to arrive.
    """

    session_id: UUID
    raw_description: str
    domain: Domain | None
    functions: list[Function]
    forms: list[Form]
    mapping_status: MappingStatus
    attempts_remaining: int
    gate: Gate | None
    posture_response: str | None
    created_at: datetime


class RevealComparison(BaseModel):
    """A session's prediction compared against its comparison set's tagged
    pattern distribution.

    Structured facts about two independently-stored things, not a
    verdict -- same framing as Student's reveal and the M6/M7 report.
    predictions is echoed back sorted by rank.
    """

    dominant_pattern: Pattern | None
    secondary_patterns: list[Pattern]
    predictions: list[PredictionEntry]
    top_prediction_is_dominant: bool
    predictions_in_secondary: list[Pattern]
    predictions_not_activated: list[Pattern]


def require_researcher_route(route: SessionRoute) -> None:
    """Reject a session that is not on the Researcher route.

    A real security/data-integrity boundary, not a cosmetic check:
    ownership alone (get_owned_session) only confirms *whose* session
    this is, not *which* flow it belongs to. Without this, a Student-route
    session_id could drive any Researcher endpoint. Every public function
    in this module takes the caller's already-loaded Session.route (the
    view fetches it via get_owned_session already; this avoids a second
    query for the same row) and checks it first, before anything else.
    """

    if route != SessionRoute.RESEARCHER:
        raise ConflictError("Session is not a Researcher-route session")


def check_mapping_status(
    domain: Domain | None,
    functions: list[Function] | None,
    forms: list[Form] | None,
) -> MappingStatus:
    """Derive a MappingStatus from the three Function/Form/Domain facets.

    A facet counts as present only if it is both non-None and non-empty --
    a null list and an empty list both count as absent. This is what keeps
    build_comparison_set's "empty functions" case defensive-only: a session
    cannot reach MAPPED or PARTIAL with an empty functions list under this
    rule, so the real flow never calls it with one.
    """

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
    route: SessionRoute,
    raw_description: str,
) -> TechnologyIntakeCreated:
    """Start a session's technology intake from its free-text description.

    One-shot: a second call for a session that already has an intake is
    rejected, same 409 pattern as Student's one-shot endpoints. This is a
    single creation call, not retried -- the retry loop lives in /tag, not
    here.
    """

    require_researcher_route(route)

    existing = (
        await session.exec(
            select(TechnologyIntake).where(TechnologyIntake.session_id == session_id)
        )
    ).first()
    if existing is not None:
        # Compute-or-fetch semantics make a retried POST safe when the first
        # response was lost. The stored description remains authoritative.
        return TechnologyIntakeCreated(
            id=existing.id,
            session_id=existing.session_id,
            raw_description=existing.raw_description,
            mapping_status=existing.mapping_status,
            created_at=existing.created_at,
        )

    record = TechnologyIntake(
        session_id=session_id,
        raw_description=raw_description,
        mapping_status=MappingStatus.UNMAPPED,
    )
    session.add(record)
    await session.commit()

    return TechnologyIntakeCreated(
        id=record.id,
        session_id=record.session_id,
        raw_description=record.raw_description,
        mapping_status=record.mapping_status,
        created_at=record.created_at,
    )


# One initial attempt plus one retry, matching the flow spec's "one
# clarification question, retry once" as exactly 2 total attempts.
MAX_TAG_ATTEMPTS = 2


def attempts_remaining(intake: TechnologyIntake) -> int:
    """How many /tag attempts this intake has left.

    Shared by submit_tag (computed right after writing a new attempt),
    get_technology_intake (computed from whatever is already stored), and
    researcher_report.py's boundary_exit check (0 remaining while not yet
    MAPPED), so none of the three drift into disagreeing about the same
    rule. Public rather than private: the same reasoning as
    contrast.py's find_counter_case_link -- a helper stops being private
    once a second module needs it.
    """

    if intake.mapping_status == MappingStatus.MAPPED:
        return 0
    return max(0, MAX_TAG_ATTEMPTS - intake.clarification_count)


async def submit_tag(
    session: AsyncSession,
    *,
    session_id: UUID,
    route: SessionRoute,
    domain: Domain | None,
    functions: list[Function],
    forms: list[Form],
) -> TagResult:
    """Record one attempt at tagging a session's technology intake.

    Bounded retry, enforced here rather than left to the frontend: at most
    MAX_TAG_ATTEMPTS calls are allowed while the intake is not yet MAPPED.
    clarification_count counts only attempts that did NOT reach MAPPED --
    a successful first call spends none of the budget. Reaching MAPPED or
    exhausting the budget both close off further calls (409); a call that
    itself exhausts the budget without reaching MAPPED still returns
    normally, since hitting the limit is a normal terminal outcome, not a
    failure of that call.
    """

    require_researcher_route(route)

    intake = (
        await session.exec(
            select(TechnologyIntake).where(TechnologyIntake.session_id == session_id)
        )
    ).first()
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
        attempts_remaining=attempts_remaining(intake),
    )


async def get_technology_intake(
    session: AsyncSession, *, session_id: UUID, route: SessionRoute
) -> TechnologyIntakeState:
    """Return the stored technology intake, so a reloaded page can resume
    mid-flow.

    404s if no intake exists yet for this session -- the ordinary "not
    started" case, exactly mirroring Student's GET /sessions/{id}/intake
    (api/services/intake.py::get_intake), which 404s the same way before
    the first diagnostic submission.
    """

    require_researcher_route(route)

    intake = (
        await session.exec(
            select(TechnologyIntake).where(TechnologyIntake.session_id == session_id)
        )
    ).first()
    if intake is None:
        raise NotFoundError("Technology intake not found")

    return TechnologyIntakeState(
        session_id=intake.session_id,
        raw_description=intake.raw_description,
        domain=intake.domain,
        functions=intake.functions or [],
        forms=intake.forms or [],
        mapping_status=intake.mapping_status,
        attempts_remaining=attempts_remaining(intake),
        gate=intake.gate,
        posture_response=intake.posture_response,
        created_at=intake.created_at,
    )


async def set_gate_and_posture(
    session: AsyncSession,
    *,
    session_id: UUID,
    route: SessionRoute,
    gate: Gate,
    posture_response: str,
) -> GateAndPostureResult:
    """Fill a mapped session's gate and posture-response fields.

    Only meaningful once mapping_status is MAPPED -- rejected otherwise,
    the same way reveal_without_a_commitment_is_rejected rejects a
    precondition that has not been met yet.

    One-shot, same discipline as Commitment/ResearcherPrediction: a second
    call is rejected once gate/posture_response are already set, not
    silently overwritten. The posture question is meant to capture a
    first genuine reflection at the moment the researcher has just
    confirmed their technology; allowing a silent overwrite would weaken
    that the same way an editable Commitment would for Student.
    """

    require_researcher_route(route)

    intake = (
        await session.exec(
            select(TechnologyIntake).where(TechnologyIntake.session_id == session_id)
        )
    ).first()
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


async def find_predictions(
    session: AsyncSession, *, session_id: UUID
) -> list[ResearcherPrediction]:
    """A session's submitted prediction, ordered by rank.

    Single source of truth for "does this session have a submitted
    prediction" and "what is it, in order" -- submit_prediction's
    existing-check, reveal_prediction_comparison, researcher_report.py,
    and researcher_case_detail.py's spoiler gate all call this rather
    than each re-deriving the same query.
    """

    return list(
        (
            await session.exec(
                select(ResearcherPrediction)
                .where(ResearcherPrediction.session_id == session_id)
                .order_by(col(ResearcherPrediction.rank))
            )
        ).all()
    )


async def submit_prediction(
    session: AsyncSession,
    *,
    session_id: UUID,
    route: SessionRoute,
    predictions: list[PredictionEntry],
) -> PredictionSubmissionResult:
    """Store a session's one-shot dual-use risk prediction.

    One-shot: a second call is rejected if any ResearcherPrediction rows
    already exist for this session, same discipline as Student's
    Commitment ("second commitment rejected"). Checked here, before
    inserting anything -- not left for the database's
    UniqueConstraint(session_id, rank)/UniqueConstraint(session_id,
    pattern) to catch; those are the safety net, not the primary check.

    Ranks must be exactly {1, 2} (for 2 entries) or {1, 2, 3} (for 3
    entries) -- consecutive, starting at 1, no gaps or duplicates. This is
    what lets /reveal's top_prediction_is_dominant assume rank 1 always
    exists and stay a plain bool, never None: nothing else guarantees a
    submitted prediction set actually includes a rank 1, since the
    UniqueConstraints only prevent duplicates, not a missing rank.
    """

    require_researcher_route(route)

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
    await session.commit()

    return PredictionSubmissionResult(predictions=predictions)


async def find_comparison_set(
    session: AsyncSession, *, session_id: UUID
) -> ComparisonSet | None:
    """Public rather than private: researcher_report.py also needs this
    lookup, the same reasoning as contrast.py's find_counter_case_link."""

    return (
        await session.exec(
            select(ComparisonSet).where(ComparisonSet.session_id == session_id)
        )
    ).first()


async def _respond(
    session: AsyncSession, comparison_set: ComparisonSet
) -> ComparisonSetResult:
    # Ordered by the persisted sequence_no, not re-derived from
    # inclusion_reason/case_id: sequence_no is written once at build time
    # from the true relevance order (shared-function count descending, then
    # domain-widened, case id as the tie-break), so this is identical on
    # the first call and on the hundredth -- nothing to reconstruct.
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
    """Published HARM cases sharing >=1 Function with `functions`.

    Ordered by shared-function count descending, case id as the
    deterministic tie-break. Empty `functions` returns immediately rather
    than running a query with an empty IN (...) clause, whose behavior
    should not be relied on.
    """

    if not functions:
        return []

    rows = (
        await session.exec(
            select(CaseTaggedFunction.case_id, func.count())
            .join(Case, col(Case.id) == col(CaseTaggedFunction.case_id))
            .where(
                col(CaseTaggedFunction.function).in_(functions),
                Case.status == CaseStatus.PUBLISHED,
                Case.case_type == CaseType.HARM,
            )
            .group_by(col(CaseTaggedFunction.case_id))
        )
    ).all()

    ordered = sorted(rows, key=lambda pair: (-pair[1], pair[0]))
    return [case_id for case_id, _ in ordered]


async def _find_domain_widen_candidates(
    session: AsyncSession, *, domain: Domain, exclude_case_ids: set[UUID]
) -> list[UUID]:
    """Published HARM cases in `domain`, excluding ones already matched.

    Ordered by case id -- already the SQL order, not re-sorted in Python.
    """

    case_ids = (
        await session.exec(
            select(Case.id)
            .where(
                Case.domain == domain,
                Case.status == CaseStatus.PUBLISHED,
                Case.case_type == CaseType.HARM,
            )
            .order_by(col(Case.id))
        )
    ).all()
    return [case_id for case_id in case_ids if case_id not in exclude_case_ids]


async def build_comparison_set(
    session: AsyncSession, *, session_id: UUID, route: SessionRoute
) -> ComparisonSetResult:
    """Match a session's technology intake against the case corpus.

    Idempotent the same way reveal_encounter/submit_diagnostic/
    submit_contrast are: an existing ComparisonSet for this session is
    returned unchanged, never recomputed.
    """

    require_researcher_route(route)

    existing = await find_comparison_set(session, session_id=session_id)
    if existing is not None:
        return await _respond(session, existing)

    intake = (
        await session.exec(
            select(TechnologyIntake).where(TechnologyIntake.session_id == session_id)
        )
    ).first()
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
    comparison_set = ComparisonSet(
        session_id=session_id,
        functions=functions,
        was_widened=was_widened,
        case_count=case_count,
    )
    session.add(comparison_set)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        existing = await find_comparison_set(session, session_id=session_id)
        if existing is None:
            raise
        return await _respond(session, existing)

    # sequence_no is each case's position in the relevance order computed
    # above (function-matched by shared-count descending, then
    # domain-widened), 0-indexed, persisted so _respond can reconstruct
    # this exact order on every later read -- not just this one.
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
    """Tally tagged-pattern frequency across `case_ids`.

    dominant is the highest count, tied broken alphabetically by Pattern
    value (A before B before C, ...) so the result never depends on
    iteration or insertion order. Empty `case_ids` skips the query
    entirely, same reasoning as _find_function_matched_cases's empty-input
    guard -- an empty IN (...) clause's behavior should not be relied on.
    """

    if not case_ids:
        return PatternDistribution(dominant=None, secondary=[], pattern_counts={})

    rows = (
        await session.exec(
            select(CaseTaggedPattern.pattern, func.count())
            .where(col(CaseTaggedPattern.case_id).in_(case_ids))
            .group_by(col(CaseTaggedPattern.pattern))
        )
    ).all()
    # ty infers `pattern` as partly an unspecialized sequence here rather
    # than plain `Pattern`, specific to selecting a raw sa_enum-backed
    # column in a multi-column tuple projection -- no other query in this
    # codebase does that. The runtime value is genuinely a Pattern; this is
    # a stub gap, not a type error, same category as config.py's.
    pattern_counts: dict[Pattern, int] = {pattern: count for pattern, count in rows}  # type: ignore

    # No tagged pattern on any matched case: a real branch (Fase 6's
    # low-activation report), not just the empty-case_ids guard above.
    if not pattern_counts:
        return PatternDistribution(dominant=None, secondary=[], pattern_counts={})

    dominant = min(
        pattern_counts, key=lambda pattern: (-pattern_counts[pattern], pattern.value)
    )
    secondary = sorted(
        (pattern for pattern in pattern_counts if pattern != dominant),
        key=lambda pattern: (-pattern_counts[pattern], pattern.value),
    )

    return PatternDistribution(
        dominant=dominant,
        secondary=secondary,
        pattern_counts=pattern_counts,
    )


async def reveal_prediction_comparison(
    session: AsyncSession, *, session_id: UUID, route: SessionRoute
) -> RevealComparison:
    """Compare a session's submitted prediction against its comparison
    set's tagged-pattern distribution.

    Recomputed on every call rather than stored behind an idempotency
    table: the distribution is deterministic over already-immutable data
    (a comparison set's cases never change once built), so recomputing is
    always safe and always identical -- unlike Student's reveal, which
    needs FeedbackRecord specifically because a commitment's verdict must
    never be recomputed differently.
    """

    require_researcher_route(route)

    comparison_set = await find_comparison_set(session, session_id=session_id)
    if comparison_set is None:
        raise ConflictError("Session has no comparison set to reveal against")

    case_ids = (
        await session.exec(
            select(ComparisonSetCase.case_id).where(
                ComparisonSetCase.comparison_set_id == comparison_set.id
            )
        )
    ).all()
    distribution = await get_pattern_distribution(session, case_ids=list(case_ids))

    prediction_rows = await find_predictions(session, session_id=session_id)
    if not prediction_rows:
        raise ConflictError("Session has no submitted prediction to reveal against")

    predictions = [
        PredictionEntry(rank=row.rank, pattern=row.pattern) for row in prediction_rows
    ]

    # predictions[0] is the rank=1 entry: ordered by rank ascending above,
    # and submit_prediction's validation guarantees rank 1 always exists.
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


async def find_set_contrast_entry(
    session: AsyncSession, *, session_id: UUID
) -> SetContrastEntry | None:
    """Public rather than private: researcher_report.py also needs this
    lookup, the same reasoning as contrast.py's find_counter_case_link."""

    return (
        await session.exec(
            select(SetContrastEntry).where(SetContrastEntry.session_id == session_id)
        )
    ).first()


async def find_set_counter_case_link(
    session: AsyncSession, *, case_ids: list[UUID]
) -> CounterCaseLink | None:
    """Whether any case in `case_ids` has a linked counter-case, as the harm case.

    Mirrors contrast.py's find_counter_case_link, but checks a whole set of
    cases rather than one -- the comparison set's contrast question is
    about the pattern across the set, not one specific case's link. Empty
    `case_ids` returns immediately, same reasoning as the other empty-input
    guards in this file. Public rather than private: researcher_report.py
    also needs this lookup.
    """

    if not case_ids:
        return None

    return (
        await session.exec(
            select(CounterCaseLink).where(
                col(CounterCaseLink.harm_case_id).in_(case_ids)
            )
        )
    ).first()


async def look_up_set_counter_case(
    session: AsyncSession, *, session_id: UUID, route: SessionRoute
) -> SetCounterCaseResponse:
    """Report whether the session's comparison set has a linked counter-case.

    Mirrors contrast.py's look_up_counter_case: a set with no counter-case
    is a valid corpus state, not an error -- this never 404s for that
    reason, only when there is no comparison set at all to check.
    """

    require_researcher_route(route)

    comparison_set = await find_comparison_set(session, session_id=session_id)
    if comparison_set is None:
        raise ConflictError("Session has no comparison set to check for a counter-case")

    case_ids = (
        await session.exec(
            select(ComparisonSetCase.case_id).where(
                ComparisonSetCase.comparison_set_id == comparison_set.id
            )
        )
    ).all()

    link = await find_set_counter_case_link(session, case_ids=list(case_ids))
    if link is None:
        return SetCounterCaseResponse(has_counter_case=False, counter_case=None)

    return SetCounterCaseResponse(
        has_counter_case=True,
        counter_case=SetCounterCaseInfo(
            counter_case_id=link.counter_case_id,
            gate_lever=link.gate_lever,
            responsibility_posture_contrast=link.responsibility_posture_contrast,
        ),
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
    route: SessionRoute,
    learner_response: str | None,
) -> SetContrastResponse:
    """Record the session's set-level contrast reflection, computing it only
    the first time.

    contrast_type is derived here from whether any case in the session's
    comparison set has a linked counter-case, never from the request. A
    non-empty learner_response is required for the twin branch, and is
    always discarded (forced to None) for the open-area branch -- same
    rule as Student's submit_contrast (api/services/contrast.py).
    Idempotent the same way that function is.
    """

    require_researcher_route(route)

    existing = await find_set_contrast_entry(session, session_id=session_id)
    if existing is not None:
        return _respond_set_contrast(existing)

    comparison_set = await find_comparison_set(session, session_id=session_id)
    if comparison_set is None:
        raise ConflictError("Session has no comparison set to contrast against")

    case_ids = (
        await session.exec(
            select(ComparisonSetCase.case_id).where(
                ComparisonSetCase.comparison_set_id == comparison_set.id
            )
        )
    ).all()

    link = await find_set_counter_case_link(session, case_ids=list(case_ids))
    if link is not None:
        if not (learner_response and learner_response.strip()):
            raise ValidationError("A reflection response is required")
        contrast_type = ContrastType.TWIN_COUNTER_CASE
        learner_response = learner_response.strip()
    else:
        contrast_type = ContrastType.OPEN_AREA
        learner_response = None

    record = SetContrastEntry(
        session_id=session_id,
        contrast_type=contrast_type,
        learner_response=learner_response,
    )
    session.add(record)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        existing = await find_set_contrast_entry(session, session_id=session_id)
        if existing is None:
            raise
        return _respond_set_contrast(existing)
    await session.commit()

    return _respond_set_contrast(record)
