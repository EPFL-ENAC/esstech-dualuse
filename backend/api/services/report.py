from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import (
    Case,
    CaseEncounter,
    Commitment,
    ContrastEntry,
    FeedbackRecord,
    SessionIntake,
)
from api.models.enums import ContrastType, Gate, MatchResult, Pattern, ScaffoldingDepth
from api.services.contrast import find_counter_case_link
from api.services.sessions import get_owned_session, require_student_route


class CompletedEncounterReport(BaseModel):
    """One encounter that reached commitment, feedback, and contrast."""

    case_title: str
    committed_pattern: Pattern
    committed_gate: Gate
    match_result: MatchResult
    contrast_type: ContrastType
    # Only set when contrast_type is TWIN_COUNTER_CASE.
    gate_lever: Gate | None = None


class MatchResultCounts(BaseModel):
    """Tally of match results across a session's completed encounters."""

    match: int
    partial_match: int
    mismatch: int


class SessionReportBody(BaseModel):
    """The debrief content, present only once at least one case is complete."""

    encounters: list[CompletedEncounterReport]
    cases_explored: int
    decision_points_considered: list[Gate]
    patterns_selected: list[Pattern]
    match_result_counts: MatchResultCounts
    counter_case_reflections_completed: int
    scaffolding_depth: ScaffoldingDepth | None = None
    # Omitted entirely (not null) when no encounter in the session has a
    # counter-case -- there is nothing real to derive it from.
    suggested_next_focus: Gate | None = None


class SessionReport(BaseModel):
    """The M6/M7 self-reflection debrief and report for a session."""

    has_completed_cases: bool
    report: SessionReportBody | None = None


@dataclass
class _EncounterState:
    """Internal grouping of one encounter's related rows, before rendering."""

    encounter: CaseEncounter
    commitment: Commitment | None
    feedback: FeedbackRecord | None
    contrast: ContrastEntry | None


async def _load_encounter_states(
    session: AsyncSession, *, session_id: UUID
) -> list[_EncounterState]:
    encounters = (
        await session.exec(
            select(CaseEncounter)
            .where(CaseEncounter.session_id == session_id)
            .order_by(col(CaseEncounter.sequence_no))
        )
    ).all()

    states = []
    for encounter in encounters:
        commitment = (
            await session.exec(
                select(Commitment)
                .where(Commitment.case_encounter_id == encounter.id)
                .order_by(desc(col(Commitment.sequence_no)))
            )
        ).first()
        feedback = (
            await session.exec(
                select(FeedbackRecord).where(
                    FeedbackRecord.case_encounter_id == encounter.id
                )
            )
        ).first()
        contrast = (
            await session.exec(
                select(ContrastEntry).where(
                    ContrastEntry.case_encounter_id == encounter.id
                )
            )
        ).first()
        states.append(
            _EncounterState(
                encounter=encounter,
                commitment=commitment,
                feedback=feedback,
                contrast=contrast,
            )
        )

    return states


async def get_session_report(
    session: AsyncSession, *, session_id: UUID, learner_id: UUID
) -> SessionReport:
    """Aggregate a session's encounters into the M6/M7 debrief and report.

    Read-only over data that never changes once written (Commitment,
    FeedbackRecord, ContrastEntry are all write-once), so there is no
    idempotency concern here the way there is for reveal or contrast.
    """

    owned_session = await get_owned_session(
        session, session_id=session_id, learner_id=learner_id
    )
    require_student_route(owned_session.route)

    states = await _load_encounter_states(session, session_id=session_id)

    # Requires all three, not just Commitment+FeedbackRecord: contrast_type
    # is a required field per listed encounter below, so an encounter can't
    # appear in the report without a ContrastEntry too. This never excludes
    # a genuinely finished case in the app's actual flow -- the
    # Another-case/Finish card in StudentEncounterPage.vue is
    # v-if="contrast", so an encounter without a contrast entry can never
    # reach /student/complete under normal navigation. The only way to see
    # this boundary is direct API/URL access mid-encounter, between reveal
    # and contrast submission, which no real user flow produces.
    completed = [
        state
        for state in states
        if state.commitment is not None
        and state.feedback is not None
        and state.contrast is not None
    ]
    if not completed:
        return SessionReport(has_completed_cases=False)

    case_ids = {state.encounter.case_id for state in completed}
    cases_by_id = {
        case.id: case
        for case in (
            await session.exec(select(Case).where(col(Case.id).in_(case_ids)))
        ).all()
    }

    encounter_reports = []
    gate_levers_by_encounter_id: dict[UUID, Gate] = {}
    for state in completed:
        commitment = state.commitment
        feedback = state.feedback
        contrast = state.contrast
        assert commitment is not None and feedback is not None and contrast is not None

        gate_lever = None
        if contrast.contrast_type == ContrastType.TWIN_COUNTER_CASE:
            link = await find_counter_case_link(
                session, case_id=state.encounter.case_id
            )
            if link is not None:
                gate_lever = link.gate_lever
                gate_levers_by_encounter_id[state.encounter.id] = gate_lever

        encounter_reports.append(
            CompletedEncounterReport(
                case_title=cases_by_id[state.encounter.case_id].title,
                committed_pattern=commitment.pattern,
                committed_gate=commitment.gate,
                match_result=feedback.match_result,
                contrast_type=contrast.contrast_type,
                gate_lever=gate_lever,
            )
        )

    match_results = [entry.match_result for entry in encounter_reports]
    match_result_counts = MatchResultCounts(
        match=match_results.count(MatchResult.MATCH),
        partial_match=match_results.count(MatchResult.PARTIAL_MATCH),
        mismatch=match_results.count(MatchResult.MISMATCH),
    )

    intake = (
        await session.exec(
            select(SessionIntake).where(SessionIntake.session_id == session_id)
        )
    ).first()
    scaffolding_depth = intake.scaffolding_depth if intake is not None else None

    suggested_next_focus = None
    for state in completed:
        gate_lever = gate_levers_by_encounter_id.get(state.encounter.id)
        if gate_lever is not None:
            suggested_next_focus = gate_lever
            break

    return SessionReport(
        has_completed_cases=True,
        report=SessionReportBody(
            encounters=encounter_reports,
            cases_explored=len(completed),
            decision_points_considered=sorted(
                {entry.committed_gate for entry in encounter_reports},
                key=lambda gate: gate.value,
            ),
            patterns_selected=sorted(
                {entry.committed_pattern for entry in encounter_reports},
                key=lambda pattern: pattern.value,
            ),
            match_result_counts=match_result_counts,
            # Derived from the same `completed` list as cases_explored, not
            # a separate scan over `states` -- contrast is already one of
            # the three conditions `completed` requires, so this is
            # structurally the same count, not one that could drift from it.
            counter_case_reflections_completed=len(completed),
            scaffolding_depth=scaffolding_depth,
            suggested_next_focus=suggested_next_focus,
        ),
    )
