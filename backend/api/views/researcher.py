from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_db_session
from api.dependencies import get_current_learner
from api.services.researcher import (
    ComparisonSetResult,
    GateAndPostureResult,
    GateAndPostureSubmission,
    PredictionSubmission,
    PredictionSubmissionResult,
    RevealComparison,
    SetContrastResponse,
    SetContrastSubmission,
    SetCounterCaseResponse,
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
from api.services.sessions import get_owned_session

router = APIRouter()


@router.post(
    "/sessions/{session_id}/researcher/intake",
    response_model=TechnologyIntakeCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Start the technology intake",
    description=(
        "Start this session's technology intake from a free-text "
        "description. One-shot: a second call for a session that already "
        "has an intake is rejected. The mapping loop happens in /tag, not "
        "here."
    ),
    tags=["Researcher"],
)
async def post_researcher_intake(
    session_id: UUID,
    body: TechnologyIntakeCreate,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> TechnologyIntakeCreated:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await create_technology_intake(
        session,
        session_id=session_id,
        route=owned_session.route,
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
    tags=["Researcher"],
)
async def get_researcher_intake(
    session_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> TechnologyIntakeState:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await get_technology_intake(
        session, session_id=session_id, route=owned_session.route
    )


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
    tags=["Researcher"],
)
async def post_researcher_tag(
    session_id: UUID,
    body: TagSubmission,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> TagResult:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await submit_tag(
        session,
        session_id=session_id,
        route=owned_session.route,
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
    tags=["Researcher"],
)
async def post_researcher_gate_and_posture(
    session_id: UUID,
    body: GateAndPostureSubmission,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> GateAndPostureResult:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await set_gate_and_posture(
        session,
        session_id=session_id,
        route=owned_session.route,
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
    tags=["Researcher"],
)
async def post_researcher_comparison_set(
    session_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> ComparisonSetResult:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await build_comparison_set(
        session, session_id=session_id, route=owned_session.route
    )


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
    tags=["Researcher"],
)
async def get_researcher_case(
    session_id: UUID,
    case_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> ResearcherCaseDetail:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await get_researcher_case_detail(
        session,
        session_id=session_id,
        case_id=case_id,
        route=owned_session.route,
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
    tags=["Researcher"],
)
async def post_researcher_prediction(
    session_id: UUID,
    body: PredictionSubmission,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> PredictionSubmissionResult:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await submit_prediction(
        session,
        session_id=session_id,
        route=owned_session.route,
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
    tags=["Researcher"],
)
async def post_researcher_reveal(
    session_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> RevealComparison:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await reveal_prediction_comparison(
        session, session_id=session_id, route=owned_session.route
    )


@router.get(
    "/sessions/{session_id}/researcher/counter-case",
    response_model=SetCounterCaseResponse,
    summary="Look up the comparison set's counter-case",
    description=(
        "Report whether any case in the session's comparison set has a "
        "linked counter-case, and if so, its gate lever and responsibility "
        "posture contrast -- shown before the contrast reflection question, "
        "the same way Student's GET /encounters/{id}/counter-case is."
    ),
    tags=["Researcher"],
)
async def get_researcher_counter_case(
    session_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> SetCounterCaseResponse:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await look_up_set_counter_case(
        session, session_id=session_id, route=owned_session.route
    )


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
    tags=["Researcher"],
)
async def post_researcher_contrast(
    session_id: UUID,
    body: SetContrastSubmission,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> SetContrastResponse:
    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    return await submit_set_contrast(
        session,
        session_id=session_id,
        route=owned_session.route,
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
    tags=["Researcher"],
)
async def get_researcher_report(
    session_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    learner_id: UUID = Depends(get_current_learner),
) -> ResearcherSessionReport:
    return await get_researcher_session_report(
        session, session_id=session_id, learner_id=learner_id
    )
