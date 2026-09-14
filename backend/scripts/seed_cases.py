"""Seed the database with non-operational demo case studies for local development.

Run after applying migrations:

    make db-upgrade
    uv run dotenv -f ../.env run python -m scripts.seed_cases
"""

import asyncio

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.db import get_engine
from api.models import (
    Case,
    CaseTaggedFunction,
    CaseTaggedGate,
    CaseTaggedPattern,
    CounterCaseLink,
)
from api.models.enums import CaseStatus, CaseType, Domain, Form, Function, Gate, Pattern


async def _seed_case(
    session: AsyncSession,
    *,
    title: str,
    area: str,
    domain: Domain,
    case_type: CaseType,
    narrative_until_crossroads: str,
    full_narrative: str,
    main_path_pattern: Pattern,
    main_path_gate: Gate,
    tagged_patterns: list[Pattern],
    tagged_gates: list[Gate],
    functions: list[Function],
    forms: list[Form],
    source_references: list[str],
) -> Case:
    """Insert a published demo case by title, or return the existing case."""
    existing = (await session.exec(select(Case).where(Case.title == title))).first()
    if existing is not None:
        # Update domain/forms if missing (migration may have added columns as nullable)
        if existing.domain is None:
            existing.domain = domain
        if existing.forms is None:
            existing.forms = forms
        await session.flush()
        return existing

    case = Case(
        title=title,
        area=area,
        domain=domain,
        case_type=case_type,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads=narrative_until_crossroads,
        full_narrative=full_narrative,
        main_path_pattern=main_path_pattern,
        main_path_gate=main_path_gate,
        forms=forms,
        source_references=source_references,
    )
    session.add(case)
    await session.flush()

    for pattern in tagged_patterns:
        session.add(CaseTaggedPattern(case_id=case.id, pattern=pattern))

    for gate in tagged_gates:
        session.add(CaseTaggedGate(case_id=case.id, gate=gate))

    for function in functions:
        session.add(CaseTaggedFunction(case_id=case.id, function=function))

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
            # Caso 1: Cyber Technologies (computing)
            harm_case_1 = await _seed_case(
                session,
                title="Demo: Sensitive Research Disclosure",
                area="research governance",
                domain=Domain.CYBER_TECHNOLOGIES,
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
                functions=[Function.COMPUTING],
                forms=[Form.PROTOCOL],
                source_references=["internal-demo-fixture-disclosure"],
            )

            # Caso 2: Cyber Technologies (computing) - counter-case del Caso 1
            counter_case_1 = await _seed_case(
                session,
                title="Demo: Staged Disclosure Review",
                area="research governance",
                domain=Domain.CYBER_TECHNOLOGIES,
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
                functions=[Function.COMPUTING],
                forms=[Form.PROTOCOL],
                source_references=["internal-demo-fixture-staged-disclosure"],
            )

            await _seed_counter_case_link(
                session,
                harm_case=harm_case_1,
                counter_case=counter_case_1,
                responsibility_posture_contrast=(
                    "The harm case treats disclosure as automatic; the counter-case "
                    "treats disclosure as a decision requiring documented review and "
                    "proportionate safeguards."
                ),
                gate_lever=Gate.G4,
            )

            # Caso 3: Robotics & Autonomous Systems (controlling)
            await _seed_case(
                session,
                title="Demo: Open Capability Release",
                area="autonomous systems",
                domain=Domain.ROBOTICS_AUTONOMOUS,
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
                functions=[Function.CONTROLLING],
                forms=[Form.PLATFORM],
                source_references=["internal-demo-fixture-open-release"],
            )

            # Caso 4: Artificial Intelligence (generating) - necessario per terzo encounter
            await _seed_case(
                session,
                title="Demo: Synthetic Media Toolkit",
                area="generative media",
                domain=Domain.ARTIFICIAL_INTELLIGENCE,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A small team must decide how to distribute a toolkit for "
                    "generating realistic synthetic voice and video."
                ),
                full_narrative=(
                    "The toolkit ships with no provenance watermarking and no consent "
                    "verification step, so downstream use is indistinguishable from "
                    "genuine recordings."
                ),
                main_path_pattern=Pattern.C,
                main_path_gate=Gate.G5,
                tagged_patterns=[Pattern.C, Pattern.O],
                tagged_gates=[Gate.G3, Gate.G5],
                functions=[Function.GENERATING],
                forms=[Form.MODEL],
                source_references=["internal-demo-fixture-synthetic-media"],
            )

            # Casi 5-9: Artificial Intelligence (generating) - 5 nuovi casi
            # Caso 5: AI con generating + editing
            await _seed_case(
                session,
                title="Demo: Automated Research Paper Generator",
                area="automated content generation",
                domain=Domain.ARTIFICIAL_INTELLIGENCE,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A team develops an AI system that can generate complete research "
                    "papers from minimal input specifications."
                ),
                full_narrative=(
                    "The system is deployed as a service with no content verification, "
                    "enabling mass production of low-quality or fabricated research."
                ),
                main_path_pattern=Pattern.I,
                main_path_gate=Gate.G4,
                tagged_patterns=[Pattern.I],
                tagged_gates=[Gate.G4],
                functions=[Function.GENERATING, Function.EDITING],
                forms=[Form.MODEL],
                source_references=["internal-demo-fixture-paper-generator"],
            )

            # Caso 6: AI con generating
            await _seed_case(
                session,
                title="Demo: Synthetic Voice Cloning Service",
                area="voice synthesis",
                domain=Domain.ARTIFICIAL_INTELLIGENCE,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A startup offers voice cloning from short audio samples with "
                    "no consent verification."
                ),
                full_narrative=(
                    "The service enables creation of realistic voice forgeries without "
                    "the subject's knowledge or approval."
                ),
                main_path_pattern=Pattern.I,
                main_path_gate=Gate.G5,
                tagged_patterns=[Pattern.I],
                tagged_gates=[Gate.G5],
                functions=[Function.GENERATING],
                forms=[Form.PLATFORM],
                source_references=["internal-demo-fixture-voice-cloning"],
            )

            # Caso 7: AI con generating + sensing
            await _seed_case(
                session,
                title="Demo: Media Authenticity Tool",
                area="media verification",
                domain=Domain.ARTIFICIAL_INTELLIGENCE,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A tool claims to detect synthetic media but can also be used to "
                    "identify weaknesses in detection systems."
                ),
                full_narrative=(
                    "The dual-use nature enables adversaries to test and improve their "
                    "synthetic content against known detection methods."
                ),
                main_path_pattern=Pattern.I,
                main_path_gate=Gate.G3,
                tagged_patterns=[Pattern.I],
                tagged_gates=[Gate.G3],
                functions=[Function.GENERATING, Function.SENSING],
                forms=[Form.MODEL],
                source_references=["internal-demo-fixture-authenticity"],
            )

            # Caso 8: AI con generating + optimizing
            await _seed_case(
                session,
                title="Demo: Synthetic Dataset Augmentation Pipeline",
                area="data augmentation",
                domain=Domain.ARTIFICIAL_INTELLIGENCE,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A pipeline generates synthetic training data to augment limited "
                    "real-world datasets."
                ),
                full_narrative=(
                    "The synthetic data may encode biases or artifacts that propagate "
                    "into downstream models trained on the augmented dataset."
                ),
                main_path_pattern=Pattern.I,
                main_path_gate=Gate.G3,
                tagged_patterns=[Pattern.I],
                tagged_gates=[Gate.G3],
                functions=[Function.GENERATING, Function.OPTIMIZING],
                forms=[Form.DATASET, Form.METHOD],
                source_references=["internal-demo-fixture-dataset-augmentation"],
            )

            # Caso 9: AI con generating + predicting
            await _seed_case(
                session,
                title="Demo: Content Personalization Engine",
                area="personalized content",
                domain=Domain.ARTIFICIAL_INTELLIGENCE,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "An engine generates personalized content at scale based on user "
                    "behavioral profiles."
                ),
                full_narrative=(
                    "The system enables targeted messaging that adapts to individual "
                    "psychological profiles without transparent disclosure."
                ),
                main_path_pattern=Pattern.K,
                main_path_gate=Gate.G6,
                tagged_patterns=[Pattern.K],
                tagged_gates=[Gate.G6],
                functions=[Function.GENERATING, Function.PREDICTING],
                forms=[Form.MODEL],
                source_references=["internal-demo-fixture-personalization"],
            )

            # Casi 10-14: Neurotechnology (5 casi, Function variate)
            # Caso 10: Neurotechnology con controlling
            await _seed_case(
                session,
                title="Demo: Neural Interface Control Module",
                area="brain-computer interface",
                domain=Domain.NEUROTECHNOLOGY,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A module enables direct command override of devices via neural "
                    "interface signals."
                ),
                full_narrative=(
                    "The capability allows bypassing traditional safety interlocks "
                    "through direct neural control pathways."
                ),
                main_path_pattern=Pattern.H,
                main_path_gate=Gate.G6,
                tagged_patterns=[Pattern.H],
                tagged_gates=[Gate.G6],
                functions=[Function.CONTROLLING],
                forms=[Form.DEVICE],
                source_references=["internal-demo-fixture-neural-control"],
            )

            # Caso 11: Neurotechnology con sensing + predicting
            await _seed_case(
                session,
                title="Demo: Cognitive State Classifier",
                area="emotion recognition",
                domain=Domain.NEUROTECHNOLOGY,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A classifier infers emotional and cognitive states from neural "
                    "signals."
                ),
                full_narrative=(
                    "The system enables inference of internal states without explicit "
                    "consent or awareness of the subject."
                ),
                main_path_pattern=Pattern.E,
                main_path_gate=Gate.G3,
                tagged_patterns=[Pattern.E],
                tagged_gates=[Gate.G3],
                functions=[Function.SENSING, Function.PREDICTING],
                forms=[Form.DEVICE, Form.DATASET],
                source_references=["internal-demo-fixture-emotion-classifier"],
            )

            # Caso 12: Neurotechnology con optimizing
            await _seed_case(
                session,
                title="Demo: Cognitive Enhancement Protocol",
                area="cognitive optimization",
                domain=Domain.NEUROTECHNOLOGY,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A protocol optimizes cognitive performance through targeted "
                    "neural modulation."
                ),
                full_narrative=(
                    "The enhancement may create dependency or unintended side effects "
                    "on long-term cognitive function."
                ),
                main_path_pattern=Pattern.F,
                main_path_gate=Gate.G5,
                tagged_patterns=[Pattern.F],
                tagged_gates=[Gate.G5],
                functions=[Function.OPTIMIZING],
                forms=[Form.DEVICE],
                source_references=["internal-demo-fixture-cognitive-enhancement"],
            )

            # Caso 13: Neurotechnology con sensing
            await _seed_case(
                session,
                title="Demo: Neural Dataset Release",
                area="neural data sharing",
                domain=Domain.NEUROTECHNOLOGY,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A research group releases a dataset of neural recordings with "
                    "minimal anonymization."
                ),
                full_narrative=(
                    "The dataset may enable re-identification of subjects or inference "
                    "of sensitive attributes from neural patterns."
                ),
                main_path_pattern=Pattern.O,
                main_path_gate=Gate.G3,
                tagged_patterns=[Pattern.O],
                tagged_gates=[Gate.G3],
                functions=[Function.SENSING],
                forms=[Form.DATASET],
                source_references=["internal-demo-fixture-neural-dataset"],
            )

            # Caso 14: Neurotechnology con controlling + editing
            await _seed_case(
                session,
                title="Demo: Behavioral Modulation Protocol",
                area="behavioral modulation",
                domain=Domain.NEUROTECHNOLOGY,
                case_type=CaseType.HARM,
                narrative_until_crossroads=(
                    "A protocol modifies behavioral patterns through targeted "
                    "neurostimulation."
                ),
                full_narrative=(
                    "The intervention enables modification of decision-making patterns "
                    "without transparent disclosure or consent mechanisms."
                ),
                main_path_pattern=Pattern.J,
                main_path_gate=Gate.G2,
                tagged_patterns=[Pattern.J],
                tagged_gates=[Gate.G2],
                functions=[Function.CONTROLLING, Function.EDITING],
                forms=[Form.PROTOCOL],
                source_references=["internal-demo-fixture-neurostimulation"],
            )

    print("Seeded demo cases.")


if __name__ == "__main__":
    asyncio.run(seed())
