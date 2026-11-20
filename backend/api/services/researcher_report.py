from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models.enums import (
    ContrastType,
    Domain,
    Form,
    Function,
    Gate,
    MappingStatus,
    Pattern,
)
from api.services.contrast import find_counter_case_link
from api.services.researcher import PredictionEntry, get_pattern_distribution
from api.services.researcher_queries import (
    attempts_remaining,
    comparison_case_ids,
    find_predictions,
    find_set_contrast_entry,
    find_technology_intake,
    require_comparison_set,
)


class ResearcherSessionReport(BaseModel):
    """The Researcher-route debrief over a session's technology intake,
    comparison set, prediction, and set-level contrast.

    trace_completeness marks how far the trace reached, not a score:
    "full" (reached contrast, with a dominant pattern), "zero_pattern"
    (reached contrast, but no pattern activated across the set -- a real
    corpus-limit branch, not an error), "boundary_exit" (mapping could not
    be completed within the attempt budget), or "in_progress".

    A None field means "not reached yet" and is omitted from the response;
    an empty list (e.g. secondary_patterns=[]) is a genuine result.
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


async def get_researcher_session_report(
    session: AsyncSession, *, session_id: UUID
) -> ResearcherSessionReport:
    """Aggregate a Researcher session's trace into its debrief and report."""

    intake = await find_technology_intake(session, session_id=session_id)
    if intake is None or intake.mapping_status != MappingStatus.MAPPED:
        if intake is not None and attempts_remaining(intake) == 0:
            return ResearcherSessionReport(
                trace_completeness="boundary_exit",
                domain=intake.domain,
                functions=intake.functions,
                forms=intake.forms,
            )
        return ResearcherSessionReport(trace_completeness="in_progress")

    contrast = await find_set_contrast_entry(session, session_id=session_id)
    if contrast is None:
        return ResearcherSessionReport(trace_completeness="in_progress")

    comparison_set = await require_comparison_set(session, session_id=session_id)
    case_ids = await comparison_case_ids(session, session_id=session_id)
    distribution = await get_pattern_distribution(session, case_ids=case_ids)

    prediction_rows = await find_predictions(session, session_id=session_id)
    predictions = [
        PredictionEntry(rank=row.rank, pattern=row.pattern) for row in prediction_rows
    ]

    gate_lever = None
    if contrast.contrast_type == ContrastType.TWIN_COUNTER_CASE:
        link = await find_counter_case_link(session, case_ids=case_ids)
        if link is not None:
            gate_lever = link.gate_lever

    if distribution.dominant is None:
        trace_completeness: Literal["full", "zero_pattern"] = "zero_pattern"
        top_prediction_is_dominant = None
    else:
        trace_completeness = "full"
        # A contrast without a prediction is reachable via direct API
        # calls (the UI gates reveal behind the prediction).
        top_prediction_is_dominant = (
            predictions[0].pattern == distribution.dominant if predictions else None
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
    )
