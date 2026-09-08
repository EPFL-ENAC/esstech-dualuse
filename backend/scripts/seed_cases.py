"""Seed the database with non-operational demo case studies for local development.

Run after applying migrations:

    make db-upgrade
    uv run dotenv -f ../.env run python -m scripts.seed_cases
"""

import asyncio

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_engine
from api.models import Case, CaseTaggedGate, CaseTaggedPattern, CounterCaseLink
from api.models.enums import CaseStatus, CaseType, Gate, Pattern


async def _seed_case(
    session: AsyncSession,
    *,
    title: str,
    area: str,
    case_type: CaseType,
    narrative_until_crossroads: str,
    full_narrative: str,
    main_path_pattern: Pattern,
    main_path_gate: Gate,
    tagged_patterns: list[Pattern],
    tagged_gates: list[Gate],
    source_references: list[str],
) -> Case:
    """Insert a published demo case by title, or return the existing case."""
    existing = (
        await session.exec(select(Case).where(Case.title == title))
    ).first()
    if existing is not None:
        return existing

    case = Case(
        title=title,
        area=area,
        case_type=case_type,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads=narrative_until_crossroads,
        full_narrative=full_narrative,
        main_path_pattern=main_path_pattern,
        main_path_gate=main_path_gate,
        source_references=source_references,
    )
    session.add(case)
    await session.flush()

    for pattern in tagged_patterns:
        session.add(CaseTaggedPattern(case_id=case.id, pattern=pattern))

    for gate in tagged_gates:
        session.add(CaseTaggedGate(case_id=case.id, gate=gate))

    return case


async def _seed_counter_case_link(
    session: AsyncSession,
    *,
    harm_case: Case,
    counter_case: Case,
    responsibility_posture_contrast: str,
    gate_lever: Gate,
) -> None:
    """Create the harm/counter-case relation once for this exact pair."""
    existing = (
        await session.exec(
            select(CounterCaseLink).where(
                CounterCaseLink.harm_case_id == harm_case.id,
                CounterCaseLink.counter_case_id == counter_case.id,
            )
        )
    ).first()
    if existing is not None:
        return

    session.add(
        CounterCaseLink(
            harm_case_id=harm_case.id,
            counter_case_id=counter_case.id,
            responsibility_posture_contrast=responsibility_posture_contrast,
            gate_lever=gate_lever,
        )
    )


async def seed() -> None:
    engine = get_engine()

    async with AsyncSession(engine) as session:
        async with session.begin():
            harm_case = await _seed_case(
                session,
                title="Demo: Sensitive Research Disclosure",
                area="research governance",
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A university research team must decide whether to publish all "
                    "technical implementation details of a capability with plausible "
                    "harmful downstream uses."
                ),
                full_narrative=(
                    "The team releases detailed implementation information before "
                    "completing an institutional review of foreseeable misuse and "
                    "appropriate access safeguards."
                ),
                main_path_pattern=Pattern.M,
                main_path_gate=Gate.G4,
                tagged_patterns=[Pattern.M, Pattern.N],
                tagged_gates=[Gate.G4, Gate.G5],
                source_references=["internal-demo-fixture-disclosure"],
            )

            counter_case = await _seed_case(
                session,
                title="Demo: Staged Disclosure Review",
                area="research governance",
                case_type=CaseType.COUNTER_CASE,
                narrative_until_crossroads=(
                    "A university research team submits a potentially sensitive "
                    "publication for independent review before release."
                ),
                full_narrative=(
                    "The review recommends a staged publication approach and access "
                    "controls. The team documents the decision and releases material "
                    "only after the relevant safeguards are in place."
                ),
                main_path_pattern=Pattern.O,
                main_path_gate=Gate.G4,
                tagged_patterns=[Pattern.O, Pattern.N],
                tagged_gates=[Gate.G4, Gate.G5],
                source_references=["internal-demo-fixture-staged-disclosure"],
            )

            await _seed_counter_case_link(
                session,
                harm_case=harm_case,
                counter_case=counter_case,
                responsibility_posture_contrast=(
                    "The harm case treats disclosure as automatic; the counter-case "
                    "treats disclosure as a decision requiring documented review and "
                    "proportionate safeguards."
                ),
                gate_lever=Gate.G4,
            )

            await _seed_case(
                session,
                title="Demo: Open Capability Release",
                area="autonomous systems",
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A development team must decide whether to release a general-purpose "
                    "coordination capability openly or apply access conditions."
                ),
                full_narrative=(
                    "The capability is released without documented use restrictions or "
                    "technical safeguards, enabling reuse outside the original context."
                ),
                main_path_pattern=Pattern.B,
                main_path_gate=Gate.G5,
                tagged_patterns=[Pattern.B, Pattern.H],
                tagged_gates=[Gate.G4, Gate.G5],
                source_references=["internal-demo-fixture-open-release"],
            )

    print("Seeded demo cases.")


if __name__ == "__main__":
    asyncio.run(seed())