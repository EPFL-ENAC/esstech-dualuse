from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import ComparisonSetCase, TechnologyIntake
from api.models.enums import (
    ContrastType,
    Domain,
    Form,
    Function,
    Gate,
    MappingStatus,
    Pattern,
)
from api.services.researcher import (
    PredictionEntry,
    attempts_remaining,
    find_comparison_set,
    find_predictions,
    find_set_contrast_entry,
    find_set_counter_case_link,
    get_pattern_distribution,
    require_researcher_route,
)
from api.services.sessions import get_owned_session


class ResearcherSessionReport(BaseModel):
    """The Researcher-route debrief: a read-only aggregation over a
    session's technology intake, comparison set, prediction, and
    set-level contrast -- all write-once past their respective steps, so
    there is no idempotency concern here, the same reasoning as Student's
    get_session_report (api/services/report.py).

    trace_completeness marks how far the session's trace actually
    reached, not a score: "full" (reached contrast, with an activated
    dominant pattern), "zero_pattern" (reached contrast, but no pattern
    was dominant across the comparison set -- a real corpus-limit
    branch, not an error), "boundary_exit" (mapping could not be
    completed within the attempt budget), or "in_progress" (has not
    reached contrast yet, for any reason).

    Every field below is None, and omitted from the response entirely
    (response_model_exclude_none on the view), unless trace_completeness
    has actually reached the point that field is meaningful -- None
    means "not reached yet", never "empty result". A list-typed field can
    still legitimately be an empty list once its point is reached (e.g.
    secondary_patterns=[] in a real "full" report where nothing
    secondary activated); that is a genuine result, distinct from None.
    """

    trace_completeness: Literal["full", "boundary_exit", "zero_pattern", "in_progress"]
    domain: Domain | None = None
    functions: list[Function] | None = None
    forms: list[Form] | None = None
    gate: Gate | None = None
    posture_response: str | None = None
    case_count: int | None = None
    was_widened: bool | None = None
    predictions: list[PredictionEntry] | None = None
    dominant_pattern: Pattern | None = None
    secondary_patterns: list[Pattern] | None = None
    top_prediction_is_dominant: bool | None = None
    contrast_type: ContrastType | None = None
    learner_response: str | None = None
    gate_lever: Gate | None = None
    reflection_prompt_key: str | None = None


async def get_researcher_session_report(
    session: AsyncSession, *, session_id: UUID, learner_id: UUID
) -> ResearcherSessionReport:
    """Aggregate a Researcher session's trace into its debrief and report.

    Read-only over data that never changes once written, so there is
    nothing to recompute-or-fetch here the way build_comparison_set/
    reveal_prediction_comparison/submit_set_contrast have to.
    """

    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    require_researcher_route(owned_session.route)

    intake = (
        await session.exec(
            select(TechnologyIntake).where(TechnologyIntake.session_id == session_id)
        )
    ).first()
    if intake is None or intake.mapping_status != MappingStatus.MAPPED:
        if intake is not None and attempts_remaining(intake) == 0:
            return ResearcherSessionReport(
                trace_completeness="boundary_exit",
                domain=intake.domain,
                functions=intake.functions,
                forms=intake.forms,
                reflection_prompt_key="researcherReflectionBoundaryExit",
            )
        return ResearcherSessionReport(trace_completeness="in_progress")

    contrast = await find_set_contrast_entry(session, session_id=session_id)
    if contrast is None:
        return ResearcherSessionReport(trace_completeness="in_progress")

    # Guaranteed to exist: submit_set_contrast itself requires a
    # ComparisonSet before it will ever write a SetContrastEntry.
    comparison_set = await find_comparison_set(session, session_id=session_id)
    assert comparison_set is not None

    case_ids = (
        await session.exec(
            select(ComparisonSetCase.case_id).where(
                ComparisonSetCase.comparison_set_id == comparison_set.id
            )
        )
    ).all()
    distribution = await get_pattern_distribution(session, case_ids=list(case_ids))

    prediction_rows = await find_predictions(session, session_id=session_id)
    predictions = [
        PredictionEntry(rank=row.rank, pattern=row.pattern) for row in prediction_rows
    ]

    gate_lever = None
    if contrast.contrast_type == ContrastType.TWIN_COUNTER_CASE:
        link = await find_set_counter_case_link(session, case_ids=list(case_ids))
        if link is not None:
            gate_lever = link.gate_lever

    if distribution.dominant is None:
        trace_completeness: Literal["full", "zero_pattern"] = "zero_pattern"
        top_prediction_is_dominant = None
        reflection_prompt_key = "researcherReflectionZeroPattern"
    else:
        trace_completeness = "full"
        # predictions[0] is the rank=1 entry, the same assumption
        # reveal_prediction_comparison makes -- except unlike reveal,
        # submit_set_contrast never itself checks that a prediction
        # exists before allowing a contrast entry, so a prediction-less
        # contrast is reachable in principle via direct API calls (never
        # through the real UI, which gates reveal behind isPredicted).
        # Guarded rather than indexed unconditionally, so that
        # theoretical path degrades to "nothing to compare" instead of a
        # 500.
        top_prediction_is_dominant = (
            predictions[0].pattern == distribution.dominant if predictions else None
        )
        reflection_prompt_key = (
            "researcherReflectionFullMatchesDominant"
            if top_prediction_is_dominant
            else "researcherReflectionFullDoesNotMatch"
        )

    return ResearcherSessionReport(
        trace_completeness=trace_completeness,
        domain=intake.domain,
        functions=intake.functions,
        forms=intake.forms,
        gate=intake.gate,
        posture_response=intake.posture_response,
        case_count=comparison_set.case_count,
        was_widened=comparison_set.was_widened,
        predictions=predictions,
        dominant_pattern=distribution.dominant,
        secondary_patterns=distribution.secondary,
        top_prediction_is_dominant=top_prediction_is_dominant,
        contrast_type=contrast.contrast_type,
        learner_response=contrast.learner_response,
        gate_lever=gate_lever,
        reflection_prompt_key=reflection_prompt_key,
    )
