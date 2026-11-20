from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.dependencies import get_researcher_session
from api.models import Session
from api.services.contrast import CounterCaseResponse
from api.services.researcher import (
    ComparisonSetResult,
    GateAndPostureResult,
    GateAndPostureSubmission,
    PredictionSubmission,
    PredictionSubmissionResult,
    RevealComparison,
    SetContrastResponse,
    SetContrastSubmission,
    TagResult,
    TagSubmission,
    TechnologyIntakeCreate,
    TechnologyIntakeCreated,
    TechnologyIntakeState,
    build_comparison_set,
    create_technology_intake,
    get_technology_intake,
    look_up_set_counter_case,
    reveal_prediction_comparison,
    set_gate_and_posture,
    submit_prediction,
    submit_set_contrast,
    submit_tag,
)
from api.services.researcher_case_detail import (
    ResearcherCaseDetail,
    get_researcher_case_detail,
)
from api.services.researcher_report import (
    ResearcherSessionReport,
    get_researcher_session_report,
)

router = APIRouter(tags=["Researcher"])


@router.post(
    "/sessions/{session_id}/researcher/intake",
    response_model=TechnologyIntakeCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Start the technology intake",
    description=(
        "Start this session's technology intake from a free-text "
        "description. Repeating the call returns the stored intake without "
        "overwriting it. The mapping loop happens in /tag, not here."
    ),
)
async def post_researcher_intake(
    body: TechnologyIntakeCreate,
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> TechnologyIntakeCreated:
    return await create_technology_intake(
        session,
        session_id=owned.id,
        raw_description=body.raw_description,
    )


@router.get(
    "/sessions/{session_id}/researcher/intake",
    response_model=TechnologyIntakeState,
    summary="Read the technology intake state",
    description=(
        "Return this session's stored technology intake so a reloaded page "
        "can resume mid-flow. 404s if no intake has been started yet."
    ),
)
async def get_researcher_intake(
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> TechnologyIntakeState:
    return await get_technology_intake(session, session_id=owned.id)


@router.post(
    "/sessions/{session_id}/researcher/tag",
    response_model=TagResult,
    summary="Tag the technology's Function/Form/Domain",
    description=(
        "Record one attempt at tagging the session's technology intake. "
        "Bounded: at most one initial attempt and one retry are allowed "
        "while the mapping is not yet complete; both the outcome and how "
        "many attempts remain are reported so the caller never has to "
        "track the budget itself."
    ),
)
async def post_researcher_tag(
    body: TagSubmission,
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> TagResult:
    return await submit_tag(
        session,
        session_id=owned.id,
        domain=body.domain,
        functions=body.functions,
        forms=body.forms,
    )


@router.post(
    "/sessions/{session_id}/researcher/gate-and-posture",
    response_model=GateAndPostureResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit the decision gate and responsibility posture",
    description=(
        "Fill the session's gate and posture-response fields. Only "
        "meaningful once the technology mapping is complete, and one-shot "
        "once submitted."
    ),
)
async def post_researcher_gate_and_posture(
    body: GateAndPostureSubmission,
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> GateAndPostureResult:
    return await set_gate_and_posture(
        session,
        session_id=owned.id,
        gate=body.gate,
        posture_response=body.posture_response,
    )


@router.post(
    "/sessions/{session_id}/researcher/comparison-set",
    response_model=ComparisonSetResult,
    summary="Build the comparison set",
    description=(
        "Match the session's technology intake against the case corpus. "
        "Computed once, then returned unchanged on every later call."
    ),
)
async def post_researcher_comparison_set(
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> ComparisonSetResult:
    return await build_comparison_set(session, session_id=owned.id)


@router.get(
    "/sessions/{session_id}/researcher/cases/{case_id}",
    response_model=ResearcherCaseDetail,
    response_model_exclude_none=True,
    summary="Get one case from the comparison set",
    description=(
        "Return one case from the session's comparison set, with why it "
        "was included. main_path_pattern, main_path_gate, full_narrative, "
        "and source_references are the answer key: absent until the "
        "session has a submitted prediction. 404s if case_id is not among "
        "this session's comparison-set cases."
    ),
)
async def get_researcher_case(
    case_id: UUID,
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> ResearcherCaseDetail:
    return await get_researcher_case_detail(
        session,
        session_id=owned.id,
        case_id=case_id,
    )


@router.post(
    "/sessions/{session_id}/researcher/prediction",
    response_model=PredictionSubmissionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit the dual-use risk prediction",
    description=(
        "Store the session's one-shot ranked pattern prediction (2 or 3 "
        "entries, ranks 1..N with no gaps or duplicates). A second "
        "submission for the same session is rejected."
    ),
)
async def post_researcher_prediction(
    body: PredictionSubmission,
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> PredictionSubmissionResult:
    return await submit_prediction(
        session,
        session_id=owned.id,
        predictions=body.predictions,
    )


@router.post(
    "/sessions/{session_id}/researcher/reveal",
    response_model=RevealComparison,
    summary="Reveal the prediction comparison",
    description=(
        "Compare the session's submitted prediction against its comparison "
        "set's tagged-pattern distribution. Recomputed on every call: the "
        "underlying data never changes once the comparison set and "
        "prediction exist, so there is nothing to store separately."
    ),
)
async def post_researcher_reveal(
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> RevealComparison:
    return await reveal_prediction_comparison(session, session_id=owned.id)


@router.get(
    "/sessions/{session_id}/researcher/counter-case",
    response_model=CounterCaseResponse,
    summary="Look up the comparison set's counter-case",
    description=(
        "Report whether any case in the session's comparison set has a "
        "linked counter-case, and if so, its gate lever and responsibility "
        "posture contrast, to show before the contrast reflection question."
    ),
)
async def get_researcher_counter_case(
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> CounterCaseResponse:
    return await look_up_set_counter_case(session, session_id=owned.id)


@router.post(
    "/sessions/{session_id}/researcher/contrast",
    response_model=SetContrastResponse,
    summary="Submit the post-reveal contrast reflection",
    description=(
        "Record the session-level contrast reflection: whether any case in "
        "the comparison set has a linked counter-case, and if so, the "
        "learner's reflection on it. The contrast type is derived "
        "server-side, never trusted from the request. Computed once, then "
        "returned unchanged on every later call."
    ),
)
async def post_researcher_contrast(
    body: SetContrastSubmission,
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> SetContrastResponse:
    return await submit_set_contrast(
        session,
        session_id=owned.id,
        learner_response=body.learner_response,
    )


@router.get(
    "/sessions/{session_id}/researcher/report",
    response_model=ResearcherSessionReport,
    response_model_exclude_none=True,
    summary="Get the session's reflection report",
    description=(
        "The Researcher-route debrief: a read-only aggregation over the "
        "session's technology intake, comparison set, prediction, and "
        "set-level contrast. Minimal when the trace has not reached "
        "contrast yet, rather than empty lists or zeroed counts."
    ),
)
async def get_researcher_report(
    owned: Session = Depends(get_researcher_session),
    session: AsyncSession = Depends(get_db_session),
) -> ResearcherSessionReport:
    return await get_researcher_session_report(session, session_id=owned.id)
