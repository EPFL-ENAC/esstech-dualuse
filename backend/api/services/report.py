from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import (
    Case,
    CaseEncounter,
    Commitment,
    ContrastEntry,
    CounterCaseLink,
    FeedbackRecord,
    SessionIntake,
)
from api.models.enums import (
    ContrastType,
    Domain,
    Gate,
    MatchResult,
    Pattern,
    ScaffoldingDepth,
)


class CompletedEncounterReport(BaseModel):
    """One encounter that reached commitment, feedback, and contrast."""

    case_title: str
    domain: Domain
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
    scaffolding_depth: ScaffoldingDepth | None = None
    # Omitted entirely (not null) when no encounter in the session has a
    # counter-case -- there is nothing real to derive it from.
    suggested_next_focus: Gate | None = None


class SessionReport(BaseModel):
    """The M6/M7 self-reflection debrief and report for a session."""

    has_completed_cases: bool
    report: SessionReportBody | None = None


async def get_session_report(
    session: AsyncSession, *, session_id: UUID
) -> SessionReport:
    """Aggregate a session's completed encounters into the M6/M7 debrief.

    A case counts as completed only once its contrast is submitted; the
    frontend offers Finish only after that step.
    """

    rows = (
        await session.exec(
            select(Case, Commitment, FeedbackRecord, ContrastEntry)
            .join(CaseEncounter, col(CaseEncounter.case_id) == col(Case.id))
            .join(
                FeedbackRecord,
                col(FeedbackRecord.case_encounter_id) == col(CaseEncounter.id),
            )
            .join(Commitment, col(Commitment.id) == col(FeedbackRecord.commitment_id))
            .join(
                ContrastEntry,
                col(ContrastEntry.case_encounter_id) == col(CaseEncounter.id),
            )
            .where(CaseEncounter.session_id == session_id)
            .order_by(col(CaseEncounter.sequence_no))
        )
    ).all()
    if not rows:
        return SessionReport(has_completed_cases=False)

    # The gate lever of the counter-case each learner actually reflected on,
    # as stored on the contrast entry.
    reflected_on = [c.counter_case_id for *_, c in rows if c.counter_case_id]
    gate_levers: dict[UUID | None, Gate] = {
        link.counter_case_id: link.gate_lever
        for link in (
            await session.exec(
                select(CounterCaseLink).where(
                    col(CounterCaseLink.counter_case_id).in_(reflected_on)
                )
            )
        ).all()
    }

    encounter_reports = []
    for case, commitment, feedback, contrast in rows:
        encounter_reports.append(
            CompletedEncounterReport(
                case_title=case.title,
                domain=case.domain,
                committed_pattern=commitment.pattern,
                committed_gate=commitment.gate,
                match_result=feedback.match_result,
                contrast_type=contrast.contrast_type,
                gate_lever=gate_levers.get(contrast.counter_case_id),
            )
        )

    match_results = [entry.match_result for entry in encounter_reports]
    intake = (
        await session.exec(
            select(SessionIntake).where(SessionIntake.session_id == session_id)
        )
    ).first()

    return SessionReport(
        has_completed_cases=True,
        report=SessionReportBody(
            encounters=encounter_reports,
            cases_explored=len(encounter_reports),
            decision_points_considered=sorted(
                {entry.committed_gate for entry in encounter_reports},
                key=lambda gate: gate.value,
            ),
            patterns_selected=sorted(
                {entry.committed_pattern for entry in encounter_reports},
                key=lambda pattern: pattern.value,
            ),
            match_result_counts=MatchResultCounts(
                match=match_results.count(MatchResult.MATCH),
                partial_match=match_results.count(MatchResult.PARTIAL_MATCH),
                mismatch=match_results.count(MatchResult.MISMATCH),
            ),
            scaffolding_depth=intake.scaffolding_depth if intake else None,
            suggested_next_focus=next(
                (e.gate_lever for e in encounter_reports if e.gate_lever), None
            ),
        ),
    )
