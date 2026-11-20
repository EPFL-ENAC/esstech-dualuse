"""Seed the curated dual-use case inventory for Student and Researcher routes.

Run after applying migrations:

    make db-upgrade
    make db-seed
"""

import asyncio
from typing import NamedTuple

from sqlmodel import col, select
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


class CuratedCase(NamedTuple):
    title: str
    area: str
    domain: Domain
    case_type: CaseType
    main_pattern: Pattern
    main_gate: Gate
    # Concatenated ids, e.g. "FGCD" and "G1G3".
    pattern_ids: str
    gate_ids: str
    functions: list[Function]
    forms: list[Form]
    crossroads: str
    reveal: str
    references: list[str]
    # Title of the provisional case this one replaced, archived on seeding.
    legacy_title: str

    @property
    def tagged_patterns(self) -> list[Pattern]:
        return [Pattern(value) for value in self.pattern_ids]

    @property
    def tagged_gates(self) -> list[Gate]:
        return [Gate(self.gate_ids[i : i + 2]) for i in range(0, len(self.gate_ids), 2)]


_SEEDED_FIELDS = (
    "area",
    "domain",
    "case_type",
    "status",
    "narrative_until_crossroads",
    "full_narrative",
    "main_path_pattern",
    "main_path_gate",
    "forms",
    "source_references",
)


async def _seed_case(session: AsyncSession, curated: CuratedCase) -> Case:
    """Upsert a published case by its authoritative title."""
    existing = (
        await session.exec(select(Case).where(Case.title == curated.title))
    ).first()
    incoming = Case(
        title=curated.title,
        area=curated.area,
        domain=curated.domain,
        case_type=curated.case_type,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads=curated.crossroads,
        full_narrative=curated.reveal,
        main_path_pattern=curated.main_pattern,
        main_path_gate=curated.main_gate,
        forms=curated.forms,
        source_references=curated.references,
    )
    if existing is None:
        case = incoming
        session.add(case)
    else:
        case = existing
        for field in _SEEDED_FIELDS:
            setattr(case, field, getattr(incoming, field))
        for model in (CaseTaggedPattern, CaseTaggedGate, CaseTaggedFunction):
            old_tags = (
                await session.exec(select(model).where(model.case_id == case.id))
            ).all()
            for old_tag in old_tags:
                await session.delete(old_tag)
    await session.flush()

    for pattern in curated.tagged_patterns:
        session.add(CaseTaggedPattern(case_id=case.id, pattern=pattern))
    for gate in curated.tagged_gates:
        session.add(CaseTaggedGate(case_id=case.id, gate=gate))
    for function in curated.functions:
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
        existing.responsibility_posture_contrast = responsibility_posture_contrast
        existing.gate_lever = gate_lever
        return

    session.add(
        CounterCaseLink(
            harm_case_id=harm_case.id,
            counter_case_id=counter_case.id,
            responsibility_posture_contrast=responsibility_posture_contrast,
            gate_lever=gate_lever,
        )
    )


# Source: Dual_Use_Dataset.xlsx
# The first listed pattern/gate is the provisional main path; every listed
# pattern/gate is also tagged. Narratives and Function/Form facets remain
# editorial drafts pending case-by-case review. Scores are never imported.
CURATED_CASES = [
    CuratedCase(
        "MIT Institute for Soldier Nanotechnologies (2002)",
        "protective nanomaterials",
        Domain.MATERIAL_SCIENCE,
        CaseType.HARM,
        Pattern.F,
        Gate.G2,
        "FGCD",
        "G2",
        [Function.FABRICATING],
        [Form.MATERIAL],
        "A university team is considering a long-term US Army partnership to develop lightweight protective materials. Before accepting, what should it make explicit about intended applications, oversight and future review points?",
        "MIT established the Institute for Soldier Nanotechnologies in 2002 with US Army Research Office funding. Its materials research pursued soldier protection, including resilience and protective systems, while civilian applications remained possible. The continuing partnership made the intended defence application visible at the funding decision—not a hidden downstream surprise.",
        [
            "MIT ISN main page — https://isn.mit.edu/",
            "MIT News — ISN overview — https://news.mit.edu/2002/nanosoldier-0320",
        ],
        "MIT Institute for Soldier Nanotechnologies",
    ),
    CuratedCase(
        "Markforged — continuous-fibre 3D printing (MIT spin-out, 2013)",
        "additive manufacturing",
        Domain.MATERIAL_SCIENCE,
        CaseType.HARM,
        Pattern.A,
        Gate.G5,
        "ABNCDE",
        "G5G6",
        [Function.FABRICATING],
        [Form.PLATFORM, Form.MATERIAL],
        "A composite-printing technique is becoming a distributed industrial product. How should its release and customer access account for uses beyond the original laboratory?",
        "The printing platform moved into defence logistics as well as civilian manufacturing. The case illustrates how a broadly useful fabrication capability can travel into military supply chains.",
        [
            "Markforged continuous fiber tech page — https://markforged.com/materials/continuous-fibers/continuous-carbon-fiber"
        ],
        "Markforged continuous-fibre 3D printing",
    ),
    CuratedCase(
        "University of Manchester — graphene body armour and military composites (2010)",
        "graphene materials",
        Domain.MATERIAL_SCIENCE,
        CaseType.HARM,
        Pattern.F,
        Gate.G1,
        "FACE",
        "G1G2",
        [Function.FABRICATING],
        [Form.MATERIAL],
        "A graphene programme considers protective and electromagnetic material applications. Which intended users should shape the research question?",
        "Graphene composite research has civilian and defence-relevant applications, including protective materials and coatings. The same properties can support different end uses.",
        [
            "University of Manchester Graphene Institute — https://www.graphene.manchester.ac.uk/",
            "PMC — Graphene composites armor review — https://pmc.ncbi.nlm.nih.gov/articles/PMC8151629/",
        ],
        "University of Manchester graphene composites",
    ),
    CuratedCase(
        "NIEHS Nano GO Consortium — Interlaboratory Nanomaterial Toxicology (Bonner/NC State, 2013)",
        "nanomaterial safety",
        Domain.MATERIAL_SCIENCE,
        CaseType.COUNTER_CASE,
        Pattern.M,
        Gate.G3,
        "MO",
        "G3G4",
        [Function.SENSING],
        [Form.METHOD, Form.PROTOCOL],
        "Engineered nanomaterials are moving toward wider use while their inhalation effects remain uncertain. Researchers across several institutions must decide how to investigate potential hazards and when to communicate findings. What should be coordinated before those materials become routine in workplaces?",
        "The NIEHS Nano GO collaborators coordinated interlaboratory toxicology work on engineered nanomaterials and published findings on pulmonary responses. Their approach made hazard characterisation and communication part of the research process before widespread exposure, informing precautionary handling and further safety assessment.",
        [
            "PubMed — NIEHS Nano GO Consortium — https://pubmed.ncbi.nlm.nih.gov/23649427/",
            "DOI: Bonner et al. EHP 2013 — https://doi.org/10.1289/ehp.1205693",
        ],
        "NIEHS Nano GO nanomaterial toxicology",
    ),
    CuratedCase(
        "RepRap — open-source 3D printing (University of Bath, 2005)",
        "desktop fabrication",
        Domain.ADVANCED_MANUFACTURING,
        CaseType.HARM,
        Pattern.B,
        Gate.G5,
        "BAND",
        "G5G1",
        [Function.FABRICATING],
        [Form.DEVICE, Form.PLATFORM],
        "An academic team considers openly releasing a low-cost, reproducible fabrication platform. What changes when many others can make and modify it?",
        "RepRap helped make desktop 3D printing widely accessible. The resulting ecosystem supported many beneficial projects but also made weapon-related fabrication easier to attempt.",
        ["RepRap project wiki — https://reprap.org/wiki/RepRap"],
        "RepRap open-source 3D printing",
    ),
    CuratedCase(
        "Fraunhofer IAPT — laser metal deposition for defence (Hamburg, 2017)",
        "industrial metal printing",
        Domain.ADVANCED_MANUFACTURING,
        CaseType.HARM,
        Pattern.F,
        Gate.G2,
        "FAD",
        "G2G6",
        [Function.FABRICATING],
        [Form.METHOD, Form.PLATFORM],
        "An additive-manufacturing institute explores industrial partnerships around aerospace repair. What downstream uses should be discussed at partnership formation?",
        "Metal additive-manufacturing methods suitable for aerospace repair can also enter defence production and maintenance pipelines. Partnership choices shape that trajectory.",
        ["Fraunhofer IAPT main page — https://www.iapt.fraunhofer.de/en.html"],
        "Fraunhofer IAPT metal additive manufacturing",
    ),
    CuratedCase(
        "PRIF Risk Assessment of 3D Firearms (Peace Research Institute Frankfurt, 2017)",
        "fabrication governance",
        Domain.ADVANCED_MANUFACTURING,
        CaseType.COUNTER_CASE,
        Pattern.O,
        Gate.G4,
        "OB",
        "G4G1",
        [Function.FABRICATING],
        [Form.METHOD],
        "Researchers studying distributed 3D printing can investigate misuse pathways before they become routine. What should an early assessment disclose?",
        "The assessment examined the proliferation implications of 3D-printed firearms and discussed possible safeguards, offering an anticipatory response to accessible fabrication.",
        [
            "PRIF — 3D printing and international security — https://www.prif.org/publikationen/publikationssuche/publikation/3d-printing-and-international-security"
        ],
        "PRIF assessment of 3D-printed firearms",
    ),
    CuratedCase(
        "EPFL LANES — 2D MoS₂ transistors (Andras Kis)",
        "semiconductor devices",
        Domain.SEMICONDUCTORS_NANOTECH,
        CaseType.HARM,
        Pattern.A,
        Gate.G1,
        "AE",
        "G1G4",
        [Function.COMPUTING],
        [Form.DEVICE, Form.MATERIAL],
        "A laboratory develops very low-power transistors for future electronics. How should researchers frame possible uses when the component is highly general-purpose?",
        "The work advanced two-dimensional transistor research. Miniaturised, efficient electronics can support civilian devices and defence or surveillance systems; the latter is a possible application, not an attributed deployment of this specific result.",
        [
            "EPFL LANES — MoS2 research page — https://www.epfl.ch/labs/lanes/news/mos2fet-news/",
            "Nature Nanotechnology 2011 — Radisavljevic et al — https://infoscience.epfl.ch/record/164049",
        ],
        "EPFL LANES two-dimensional MoS₂ transistors",
    ),
    CuratedCase(
        "TU Eindhoven → ASML — the EUV academic pipeline",
        "semiconductor manufacturing",
        Domain.SEMICONDUCTORS_NANOTECH,
        CaseType.HARM,
        Pattern.L,
        Gate.G6,
        "LHD",
        "G6G2",
        [Function.FABRICATING],
        [Form.INFRASTRUCTURE],
        "Academic research feeds a specialised industrial lithography ecosystem. What responsibilities arise if one capability becomes a strategic production bottleneck?",
        "EUV lithography became critical to advanced chip production, making access to equipment a subject of export controls and geopolitical leverage. The research-to-industry pipeline is one part of that wider system.",
        [
            "ASML press release — TU/e partnership — https://www.asml.com/en/news/press-releases/2023/asml-and-tue-strengthen-longstanding-collaboration"
        ],
        "TU Eindhoven–ASML EUV research pipeline",
    ),
    CuratedCase(
        "Aerosolized Nanomaterial Toxicity (Positive Counter-case, EPA/Universities, 2010s)",
        "occupational nanomaterial safety",
        Domain.SEMICONDUCTORS_NANOTECH,
        CaseType.COUNTER_CASE,
        Pattern.M,
        Gate.G3,
        "MO",
        "G3G4",
        [Function.SENSING],
        [Form.METHOD, Form.PROTOCOL],
        "Engineered nanomaterials may enter workplaces before their exposure effects are fully known. Where can safety research intervene early?",
        "Environmental-health researchers studied exposure and handling concerns around aerosolised nanomaterials, informing precautionary workplace practices.",
        [
            "Nature Nanotechnology — Poland asbestos-like pathogenicity — https://www.nature.com/articles/nnano.2008.111",
            "PubMed — Poland CNT pathogenicity — https://pubmed.ncbi.nlm.nih.gov/18654567/",
        ],
        "Aerosolised nanomaterial safety research",
    ),
    CuratedCase(
        "ImageNet — Fei-Fei Li (Princeton → Stanford, 2009)",
        "computer vision datasets",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.A,
        Gate.G3,
        "ABCDEJ",
        "G3G5",
        [Function.SENSING, Function.PREDICTING],
        [Form.DATASET],
        "A team assembles a large image benchmark from online material. What should it consider about consent, labels and downstream reuse before releasing the data?",
        "ImageNet accelerated computer-vision research. Its scale and reuse also raise questions about image consent, category design and applications beyond the benchmark's original purpose.",
        ["ImageNet CVPR 2009 paper — https://ieeexplore.ieee.org/document/5206848/"],
        "ImageNet dataset and benchmark",
    ),
    CuratedCase(
        "Joseph Redmon / YOLO — academic withdrawal (University of Washington, 2020)",
        "real-time computer vision",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.A,
        Gate.G5,
        "AIP",
        "G5G1",
        [Function.SENSING, Function.PREDICTING],
        [Form.MODEL, Form.METHOD],
        "A real-time object detector is becoming widely used. What can its creator do when adoption reaches surveillance and military contexts?",
        "Redmon publicly expressed concern about military and surveillance uses of computer vision and stepped away from that research area. His choice highlights both individual agency and its limits after a capability spreads.",
        ["Redmon et al. YOLO - CVPR 2016 — https://arxiv.org/abs/1506.02640"],
        "Joseph Redmon and YOLO object detection",
    ),
    CuratedCase(
        "Project Maven — Google/DoD AI partnership controversy (2017–18)",
        "drone imagery analysis",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.A,
        Gate.G2,
        "AFP",
        "G2G6",
        [Function.SENSING, Function.PREDICTING],
        [Form.MODEL, Form.PLATFORM],
        "An AI organisation considers a defence contract for analysing aerial imagery. Who should decide whether the work fits its stated principles?",
        "Google's Project Maven work prompted employee opposition and a later decision not to renew that contract. The dispute made partnership framing and collective researcher voice visible.",
        [
            "Project Maven - NYT article — https://www.nytimes.com/2018/05/30/technology/google-project-maven-pentagon.html"
        ],
        "Project Maven AI partnership",
    ),
    CuratedCase(
        "International AI Safety Report — Bengio et al. (Mila / Univ. Montréal, 2025–26)",
        "frontier AI governance",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.COUNTER_CASE,
        Pattern.O,
        Gate.G4,
        "OM",
        "G4G1",
        [Function.GENERATING, Function.PREDICTING],
        [Form.METHOD],
        "Frontier AI capability is advancing while its downstream effects remain uncertain. What can an independent evidence synthesis contribute before deployment?",
        "The international report assembled evidence on advanced-AI risks and uncertainty for researchers and policymakers, providing a basis for anticipatory review rather than a verdict on a single model.",
        [
            "International AI Safety Report 2026 — https://internationalaisafetyreport.org/",
            "arXiv 2501.17805 — https://arxiv.org/abs/2501.17805",
        ],
        "International AI Safety Report",
    ),
    CuratedCase(
        "EPFL MLO / SPRING — agent research in Lausanne",
        "agentic AI",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.A,
        Gate.G1,
        "AB",
        "G1G4",
        [Function.GENERATING, Function.COMPUTING],
        [Form.MODEL, Form.PLATFORM],
        "Researchers publish agentic language-model methods for beneficial automation. How should they consider repurposing before disclosure?",
        "General-purpose language-model capabilities can be adapted for fraud and phishing. The supplied inventory links this risk to academic work, but does not establish that a named EPFL lab caused a specific criminal deployment.",
        ["EPFL MLO Lab — https://www.epfl.ch/labs/mlo/"],
        "Agentic language models and cybercrime adaptation",
    ),
    CuratedCase(
        "Automated Cyber-Attack Agents (Various, 2025)",
        "agentic cybersecurity",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.G,
        Gate.G4,
        "GAB",
        "G4G3",
        [Function.COMPUTING, Function.GENERATING],
        [Form.MODEL, Form.METHOD],
        "A security team studies whether agents can automate parts of cyber operations. Which findings should be shared, and with whom?",
        "Proof-of-concept work can expose defensive weaknesses while also lowering barriers to misuse. Disclosure choices matter; this case does not include actionable implementation details.",
        ["Fang et al. arXiv 2404.08144 — https://arxiv.org/abs/2404.08144"],
        "Research on automated cyber-attack agents",
    ),
    CuratedCase(
        "MegaSyn → VX-class toxins (Urbina et al., 2022)",
        "generative chemistry",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.COUNTER_CASE,
        Pattern.M,
        Gate.G4,
        "MOG",
        "G4G3",
        [Function.GENERATING, Function.OPTIMIZING],
        [Form.MODEL, Form.METHOD],
        "A chemistry model reveals an unexpected dual-use possibility. How can a team warn others without publishing material that would make misuse easier?",
        "Urbina and colleagues reported a concerning model-use experiment while withholding sensitive outputs and implementation details, using the publication to argue for dual-use review.",
        [
            "Urbina et al. Dual Use - Nature MI 2022 — https://www.nature.com/articles/s42256-022-00465-9"
        ],
        "MegaSyn generative chemistry warning",
    ),
    CuratedCase(
        "Universal and Transferable Adversarial Suffixes (CMU, 2023)",
        "AI security research",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.M,
        Gate.G4,
        "MA",
        "G4G5",
        [Function.GENERATING, Function.COMPUTING],
        [Form.MODEL, Form.METHOD],
        "Researchers find a way to probe safety limits across multiple language models. What would responsible disclosure require?",
        "The research showed that some adversarial prompts transferred across models, revealing a robustness weakness while also raising questions about releasing attack methods.",
        [
            "Zou et al. Adversarial Suffixes arXiv 2307.15043 — https://arxiv.org/abs/2307.15043"
        ],
        "Universal adversarial suffixes for language models",
    ),
    CuratedCase(
        "Deepfake Generation via GANs (Various, 2014-Present)",
        "synthetic media",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.K,
        Gate.G1,
        "KBAE",
        "G1G5",
        [Function.GENERATING, Function.EDITING],
        [Form.MODEL, Form.PLATFORM],
        "A media-synthesis capability becomes easier to use and distribute. What access and consent safeguards should be considered before release?",
        "Generative-media advances enable creative and medical applications but can also support non-consensual imagery, impersonation and disinformation. The broad research field cannot be reduced to one responsible team.",
        [
            "Goodfellow et al., GAN paper (arxiv:1406.2661) — https://arxiv.org/abs/1406.2661"
        ],
        "Deepfake generation research",
    ),
    CuratedCase(
        "Staged Release of GPT-2 (OpenAI, 2019)",
        "language-model release",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.COUNTER_CASE,
        Pattern.O,
        Gate.G5,
        "ON",
        "G5G4",
        [Function.GENERATING],
        [Form.MODEL],
        "A lab expects a text model to be useful but potentially misused. How could release be staged while evidence is gathered?",
        "OpenAI initially limited GPT-2 access and released versions in stages while discussing misuse concerns, illustrating release design as a deliberate decision gate.",
        [
            "OpenAI GPT-2 release strategies & outcomes (arxiv) — https://arxiv.org/pdf/1908.09203"
        ],
        "Staged release of GPT-2",
    ),
    CuratedCase(
        "Ribeiro & West — Auditing YouTube radicalisation (EPFL dlab, FAT* 2020)",
        "recommender-system auditing",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.C,
        Gate.G1,
        "CM",
        "G1G4",
        [Function.PREDICTING, Function.SENSING],
        [Form.METHOD, Form.DATASET],
        "Researchers audit recommendation pathways on a large video platform. How should they present findings without overstating what the data proves?",
        "The audit examined movement between communities of political video channels. It provides evidence for discussing recommendation and user-choice dynamics, not a simple causal verdict on every viewer.",
        [
            "Ribeiro et al., YouTube radicalization (FAT* 2020) — https://dl.acm.org/doi/10.1145/3351095.3372879"
        ],
        "Ribeiro and West audit of YouTube recommendations",
    ),
    CuratedCase(
        "Aleksandr Kogan — 'thisisyourdigitallife' (University of Cambridge, 2014–15)",
        "social-data collection",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.N,
        Gate.G6,
        "NICJ",
        "G6G2",
        [Function.PREDICTING, Function.SENSING],
        [Form.DATASET, Form.PLATFORM],
        "A research app can collect information about participants and their contacts. What limits should govern sharing that data with another organisation?",
        "Data gathered through the app was transferred for political profiling associated with Cambridge Analytica, making consent, partnership and downstream control central to the case.",
        [
            "Kogan / Cambridge Analytica data scandal (Wikipedia) — https://en.wikipedia.org/wiki/Facebook%E2%80%93Cambridge_Analytica_data_scandal"
        ],
        "Aleksandr Kogan and thisisyourdigitallife",
    ),
    CuratedCase(
        "Vosoughi, Roy & Aral — 'The spread of true and false news online' (MIT, Science 2018)",
        "misinformation research",
        Domain.ARTIFICIAL_INTELLIGENCE,
        CaseType.HARM,
        Pattern.C,
        Gate.G1,
        "CM",
        "G1G4",
        [Function.SENSING, Function.PREDICTING],
        [Form.DATASET, Form.METHOD],
        "A team measures how different kinds of news spread online. How can diagnostic findings be communicated without turning them into optimisation advice?",
        "The study reported that false news spread farther and faster than true news in its dataset. Such diagnosis can inform interventions while also being misread as a playbook; the inventory does not document a specific misuse of the paper.",
        [
            "Vosoughi et al., true vs false news (Science 2018) — https://www.science.org/doi/10.1126/science.aap9559"
        ],
        "Vosoughi, Roy and Aral on false-news diffusion",
    ),
    CuratedCase(
        "Spectre & Meltdown — hardware side-channel disclosures (2018)",
        "hardware security",
        Domain.CYBER_TECHNOLOGIES,
        CaseType.COUNTER_CASE,
        Pattern.M,
        Gate.G4,
        "MOH",
        "G4",
        [Function.COMPUTING],
        [Form.DEVICE, Form.METHOD],
        "Researchers discover a serious processor-side weakness. How should they coordinate publication with vendors and defenders?",
        "The vulnerabilities were disclosed through a coordinated process that gave affected parties time to prepare mitigations before public details became available.",
        ["Spectre & Meltdown attack details & timeline — https://meltdownattack.com/"],
        "Spectre and Meltdown coordinated disclosure",
    ),
    CuratedCase(
        "DP-3T — privacy-preserving contact tracing (EPFL SPRING, 2020)",
        "privacy-preserving protocols",
        Domain.CYBER_TECHNOLOGIES,
        CaseType.COUNTER_CASE,
        Pattern.O,
        Gate.G3,
        "ON",
        "G3G5",
        [Function.SENSING, Function.COMPUTING],
        [Form.PROTOCOL],
        "A contact-tracing system is being designed under public-health pressure. Could privacy constraints be built into its method from the start?",
        "DP-3T proposed decentralised proximity matching, showing how design choices can limit central collection of social-contact data before deployment.",
        [
            "DP-3T contact tracing GitHub & documentation — https://github.com/DP-3T/documents"
        ],
        "DP-3T privacy-preserving contact tracing",
    ),
    CuratedCase(
        "Hospital Denial of Service Vulnerabilities (Various)",
        "healthcare cybersecurity",
        Domain.CYBER_TECHNOLOGIES,
        CaseType.HARM,
        Pattern.G,
        Gate.G4,
        "GM",
        "G4",
        [Function.COMPUTING, Function.SENSING],
        [Form.METHOD, Form.INFRASTRUCTURE],
        "Security researchers identify weaknesses in healthcare infrastructure. What should they verify and coordinate before making findings public?",
        "Healthcare systems have faced serious cyber incidents. The supplied inventory suggests a direct link to published academic vulnerabilities but does not document that causal chain; the teachable tension is between disclosure and remediation.",
        [
            "CISA healthcare cybersecurity guidance — https://www.cisa.gov/sites/default/files/publications/HealthCare_Cybersecurity_508.pdf"
        ],
        "Hospital cybersecurity disclosure",
    ),
    CuratedCase(
        "Wang & Kosinski — 'deep neural networks can detect sexual orientation from faces' (Stanford, 2018)",
        "sensitive biometric inference",
        Domain.CYBER_TECHNOLOGIES,
        CaseType.HARM,
        Pattern.K,
        Gate.G1,
        "KICJ",
        "G1G4",
        [Function.SENSING, Function.PREDICTING],
        [Form.MODEL, Form.DATASET],
        "Researchers consider predicting a sensitive personal trait from images. Should the question be pursued, and what would count as valid evidence and consent?",
        "The paper's claims about inferring sexual orientation from facial photographs drew methodological and ethical criticism. Even contested predictions can expose people to stigma and surveillance risk.",
        [
            "Wang & Kosinski, sexual orientation detection (JPSP 2018) — https://psycnet.apa.org/doiLanding?doi=10.1037/pspa0000098"
        ],
        "Wang and Kosinski facial-orientation inference",
    ),
    CuratedCase(
        "Uyghur-targeted face-recognition papers — academic-journal retractions (2018–21)",
        "ethnicity classification",
        Domain.CYBER_TECHNOLOGIES,
        CaseType.HARM,
        Pattern.K,
        Gate.G1,
        "KFJP",
        "G1G4",
        [Function.SENSING, Function.PREDICTING],
        [Form.MODEL, Form.DATASET],
        "A vision project proposes classifying a protected group from facial images. What should be challenged before collecting data or publishing results?",
        "Papers framed around Uyghur facial classification faced criticism and retractions, illustrating how the research question itself can create discriminatory surveillance risk.",
        [
            "Nature: ethical questions in facial recognition — https://www.nature.com/articles/d41586-020-03187-3"
        ],
        "Uyghur-targeted face-recognition papers",
    ),
    CuratedCase(
        "Clearview AI (Origins in Academic Facial Recognition, 2010s)",
        "face-search systems",
        Domain.CYBER_TECHNOLOGIES,
        CaseType.HARM,
        Pattern.K,
        Gate.G3,
        "KNBCEJ",
        "G3G6",
        [Function.SENSING, Function.PREDICTING],
        [Form.PLATFORM, Form.DATASET],
        "A face-search product is built from large collections of public images. Which permissions and customer uses need scrutiny before deployment?",
        "Clearview AI commercialised large-scale face search using scraped images, drawing legal and ethical challenges around consent and surveillance. This is a commercial deployment, not an act attributed to a specific academic inventor.",
        [
            "Clearview AI law enforcement facial recognition — https://www.clearview.ai/law-enforcement"
        ],
        "Clearview AI facial-recognition deployment",
    ),
    CuratedCase(
        "Peter Shor — polynomial-time factoring on a quantum computer (AT&T Bell Labs, 1994)",
        "quantum computing",
        Domain.QUANTUM_TECHNOLOGY,
        CaseType.HARM,
        Pattern.H,
        Gate.G1,
        "H",
        "G1G4",
        [Function.COMPUTING],
        [Form.METHOD],
        "A theoretical algorithm could eventually weaken widely used encryption. What should accompany publication when the hardware is not yet capable?",
        "Shor's algorithm established a future threat to public-key systems if sufficiently capable quantum computers become available, helping motivate a long-term cryptographic transition.",
        [
            "Shor — SIAM J. Comput. (1997) — https://epubs.siam.org/doi/10.1137/S0097539795293172",
            "Polynomial-Time Algorithms — arXiv preprint — https://arxiv.org/abs/quant-ph/9508027",
        ],
        "Shor's quantum factoring algorithm",
    ),
    CuratedCase(
        "Google Sycamore quantum supremacy paper (2019)",
        "quantum computing",
        Domain.QUANTUM_TECHNOLOGY,
        CaseType.HARM,
        Pattern.H,
        Gate.G4,
        "HC",
        "G4",
        [Function.COMPUTING],
        [Form.DEVICE, Form.METHOD],
        "A quantum-computing team prepares a high-profile capability claim. How should it explain what the result does and does not imply for security?",
        "The Sycamore experiment was a milestone on a specialised task; it did not demonstrate the ability to break deployed cryptography. Broader strategic signalling still matters.",
        [
            "Arute et al. — Quantum supremacy (Nature 2019) — https://www.nature.com/articles/s41586-019-1666-5"
        ],
        "Google Sycamore quantum-computing paper",
    ),
    CuratedCase(
        "Quantum Sensing for Stealth Detection (Various)",
        "quantum sensors",
        Domain.QUANTUM_TECHNOLOGY,
        CaseType.HARM,
        Pattern.H,
        Gate.G1,
        "HG",
        "G1G6",
        [Function.SENSING],
        [Form.DEVICE],
        "A highly sensitive sensor is developed for environmental measurement. Which other uses should be considered before the research agenda is fixed?",
        "Quantum sensing has potential civilian and defence applications. Claims that a given sensor defeats stealth systems remain contingent and should not be treated as an established outcome of generic university research.",
        [
            "Quantum sensing gravity cartography (Nature 2021) — https://www.nature.com/articles/s41586-021-04315-3"
        ],
        "Quantum sensing and stealth detection",
    ),
    CuratedCase(
        "'Bugs in our Pockets' — academic cryptographers against client-side scanning (2021)",
        "client-side scanning",
        Domain.QUANTUM_TECHNOLOGY,
        CaseType.COUNTER_CASE,
        Pattern.O,
        Gate.G4,
        "OMP",
        "G4",
        [Function.COMPUTING, Function.SENSING],
        [Form.METHOD, Form.PROTOCOL],
        "A proposed scanning system promises safety benefits but could alter private messaging at scale. What should independent cryptographers examine?",
        "Cryptographers collectively argued that client-side scanning would create significant security and surveillance risks, intervening before a proposed architecture became entrenched.",
        [
            "Abelson et al. — Bugs in Pockets (arXiv 2110.07450) — https://arxiv.org/abs/2110.07450"
        ],
        "Bugs in Our Pockets cryptography report",
    ),
    CuratedCase(
        "Post-Quantum Cryptography Standardization (Positive Counter-case, NIST/Academia, 2016-Present)",
        "quantum-resistant cryptography",
        Domain.QUANTUM_TECHNOLOGY,
        CaseType.COUNTER_CASE,
        Pattern.O,
        Gate.G3,
        "OH",
        "G3G4",
        [Function.COMPUTING],
        [Form.PROTOCOL, Form.METHOD],
        "If future quantum machines threaten today's public-key systems, when should replacement methods be designed and evaluated?",
        "Academic and standards communities developed and evaluated quantum-resistant algorithms in advance of a cryptographically relevant quantum computer, creating a path to migration.",
        [
            "NIST Post-Quantum Cryptography project — https://csrc.nist.gov/projects/post-quantum-cryptography"
        ],
        "Post-quantum cryptography standardisation",
    ),
    CuratedCase(
        "EPFL LACAL: Cryptanalytic Attacks on RSA-768 (EPFL, 2010)",
        "cryptanalysis",
        Domain.QUANTUM_TECHNOLOGY,
        CaseType.COUNTER_CASE,
        Pattern.M,
        Gate.G4,
        "MOH",
        "G4",
        [Function.COMPUTING],
        [Form.METHOD],
        "A team demonstrates a cryptographic weakness using a public challenge. What should its publication say about migration without overclaiming immediate compromise?",
        "The RSA-768 factorisation helped show limits of older key sizes and supported stronger-key migration. Publishing cryptanalytic results also informs potential adversaries.",
        [
            "Kleinjung et al. — 768-bit RSA factorization (CRYPTO 2010) — https://link.springer.com/chapter/10.1007/978-3-642-14623-7_18",
            "IACR eprint version — https://eprint.iacr.org/2010/006",
        ],
        "EPFL LACAL RSA-768 factorisation",
    ),
    CuratedCase(
        "KAIST / Hanwha 'Research Center for the Convergence of National Defense and AI' (2018 boycott)",
        "military AI research",
        Domain.ROBOTICS_AUTONOMOUS,
        CaseType.HARM,
        Pattern.F,
        Gate.G2,
        "FGP",
        "G2G1",
        [Function.CONTROLLING, Function.PREDICTING],
        [Form.MODEL, Form.PLATFORM],
        "A university considers an AI research centre with a defence contractor. What commitments about autonomous weapons should be required at the partnership gate?",
        "The announced KAIST–Hanwha centre prompted an international academic boycott and public assurances about its scope, showing how funder framing and community pressure shape research governance.",
        [
            "Open letter to KAIST — AI researchers boycott — https://cgi.cse.unsw.edu.au/~tw/ciair/kaist.html"
        ],
        "KAIST–Hanwha defence AI partnership",
    ),
    CuratedCase(
        "UPenn GRASP Lab — autonomous drone swarms (Kumar lab, 2012)",
        "autonomous robotics",
        Domain.ROBOTICS_AUTONOMOUS,
        CaseType.HARM,
        Pattern.F,
        Gate.G2,
        "FADE",
        "G2G4",
        [Function.CONTROLLING, Function.SENSING],
        [Form.DEVICE, Form.METHOD],
        "A robotics lab develops coordinated autonomous flight with mixed funders. Which foreseeable uses should be reviewed when funding and publication decisions are made?",
        "Swarm-control research can support inspection, rescue and defence applications. Funding relationships and general-purpose transfer make downstream responsibility difficult to assign to one team.",
        ["Vijay Kumar / GRASP Lab — UPenn robotics — https://www.grasp.upenn.edu/"],
        "UPenn GRASP autonomous drone swarms",
    ),
    CuratedCase(
        'Robotic "Dog" Weaponization (MIT Spin-off, 2020s)',
        "legged robotics",
        Domain.ROBOTICS_AUTONOMOUS,
        CaseType.HARM,
        Pattern.G,
        Gate.G6,
        "GAE",
        "G6G5",
        [Function.CONTROLLING],
        [Form.DEVICE, Form.PLATFORM],
        "A general-purpose quadruped robot enters the market. What restrictions or responses are available if customers attempt to weaponise it?",
        "Third parties have demonstrated armed quadruped platforms. This does not mean every legged-robotics research group endorsed that use; it exposes limits of downstream control after deployment.",
        [
            "Spot robot weaponization — IEEE Spectrum — https://spectrum.ieee.org/spot-robot-gun"
        ],
        "Weaponisation of quadruped robots",
    ),
    CuratedCase(
        "Pledge Against Weaponizing Robotics (Positive Counter-case, 2022)",
        "robotics governance",
        Domain.ROBOTICS_AUTONOMOUS,
        CaseType.COUNTER_CASE,
        Pattern.O,
        Gate.G6,
        "ONP",
        "G6G2",
        [Function.CONTROLLING],
        [Form.DEVICE, Form.PROTOCOL],
        "Robotics companies see mounting interest in adapting mobile robots for weapons. Can vendors set a collective boundary before further deployment?",
        "Several robotics companies publicly pledged not to weaponise general-purpose robots and to scrutinise customer use, a governance lever whose effectiveness depends on implementation.",
        [
            "Boston Dynamics — Anti-weaponization pledge — https://bostondynamics.com/news/general-purpose-robots-should-not-be-weaponized/"
        ],
        "Pledge against weaponising general-purpose robots",
    ),
    CuratedCase(
        "EPFL NeuroRestore / ONWARD Medical",
        "neurotechnology translation",
        Domain.NEUROTECHNOLOGY,
        CaseType.HARM,
        Pattern.A,
        Gate.G1,
        "ADE",
        "G1G6",
        [Function.SENSING, Function.CONTROLLING],
        [Form.DEVICE, Form.PLATFORM],
        "A therapeutic brain–spine interface moves from research toward clinical products. What uses and safeguards should be considered beyond the initial patient group?",
        "The programme advanced rehabilitation technologies for people with paralysis. The inventory treats broader transferability as a reflection question, not evidence that this team pursued coercive or military uses.",
        [
            "Nature Medicine 2024 — ARC-EX trial — https://www.nature.com/articles/s41591-024-02940-9",
            "NeuroRestore official page — https://www.neurorestore.swiss/press-1/arc-ex",
        ],
        "EPFL NeuroRestore and ONWARD Medical",
    ),
    CuratedCase(
        "DARPA N3 academic grantees (2019)",
        "neural-interface research",
        Domain.NEUROTECHNOLOGY,
        CaseType.HARM,
        Pattern.F,
        Gate.G2,
        "FAD",
        "G2",
        [Function.SENSING, Function.CONTROLLING],
        [Form.DEVICE, Form.METHOD],
        "Researchers are offered funding to develop non-surgical neural interfaces. How should the stated military enhancement aim affect the partnership decision?",
        "DARPA's N3 programme explicitly sought non-surgical neural interfaces for defence applications, making the intended use visible at the funding gate.",
        [
            "DARPA N3 program official page — https://www.darpa.mil/research/programs/next-generation-nonsurgical-neurotechnology"
        ],
        "DARPA N3 non-surgical neural-interface grants",
    ),
    CuratedCase(
        "Rafael Yuste & the NeuroRights Initiative (Columbia University, 2017)",
        "neurotechnology governance",
        Domain.NEUROTECHNOLOGY,
        CaseType.COUNTER_CASE,
        Pattern.O,
        Gate.G1,
        "O",
        "G1G4",
        [Function.SENSING],
        [Form.PROTOCOL, Form.METHOD],
        "Neural data and interventions raise questions about mental privacy and agency. What rights should shape the research agenda before products mature?",
        "The NeuroRights Initiative advocated governance principles for mental privacy and related interests, bringing affected-person rights into early neurotechnology discussions.",
        [
            "NeuroRights Foundation — https://www.neurorightsfoundation.org/mission",
            "Rafael Yuste NeuroTechnology Center — https://ntc.columbia.edu/rafael-yuste/",
        ],
        "NeuroRights Initiative",
    ),
    CuratedCase(
        "He Jiankui — CRISPR-edited twins (SUSTech, 2018)",
        "human genome editing",
        Domain.BIOCHEMISTRY,
        CaseType.HARM,
        Pattern.I,
        Gate.G6,
        "IB",
        "G6G3",
        [Function.EDITING],
        [Form.METHOD, Form.PROTOCOL],
        "A team proposes heritable genome editing in a clinical context. What scientific and ethical thresholds should constrain the method before any intervention?",
        "He Jiankui announced the birth of genome-edited children amid broad condemnation and subsequent legal consequences. The case centres on proceeding despite strong ethical and governance objections.",
        [
            "He Jiankui CRISPR twins affair — PMC review — https://pmc.ncbi.nlm.nih.gov/articles/PMC6813942/",
            "Science — He Jiankui timeline — https://www.science.org/content/article/crispr-bombshell-chinese-researcher-claims-have-created-gene-edited-twins",
        ],
        "He Jiankui germline-editing experiment",
    ),
    CuratedCase(
        "Horsepox synthesis (University of Alberta, 2017)",
        "synthetic biology disclosure",
        Domain.BIOCHEMISTRY,
        CaseType.HARM,
        Pattern.I,
        Gate.G3,
        "IB",
        "G3G4",
        [Function.GENERATING, Function.EDITING],
        [Form.METHOD],
        "A team synthesises a virus for research and considers publishing its methods. How should review distinguish scientific value from foreseeable misuse?",
        "The horsepox work and its publication provoked biosecurity debate about whether detailed methods could aid harmful replication. The case omits procedural details.",
        [
            "Noyce et al., PLOS ONE 2018 horsepox synthesis — https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0188453"
        ],
        "Horsepox synthesis and publication",
    ),
    CuratedCase(
        "H5N1 gain-of-function (Erasmus MC / Wisconsin, 2011–12)",
        "influenza research governance",
        Domain.BIOCHEMISTRY,
        CaseType.HARM,
        Pattern.I,
        Gate.G3,
        "IM",
        "G3G4",
        [Function.EDITING, Function.PREDICTING],
        [Form.METHOD, Form.PROTOCOL],
        "Researchers study changes to influenza transmission in animals. Which parts of the work should proceed or be disclosed under dual-use review?",
        "The H5N1 studies triggered an international debate over research benefits, biosafety and publication of sensitive findings, followed by funding and review-policy changes.",
        [
            "Herfst et al., Science 2012 H5N1 airborne — https://www.science.org/doi/10.1126/science.1213362"
        ],
        "H5N1 gain-of-function publication debate",
    ),
]


# Titles changed after the first authoritative seed. Keep the old rows for
# historical encounters, but never offer both versions as new candidates.
PREVIOUS_CURATED_TITLES = {
    "MIT Institute for Soldier Nanotechnologies (2002– )": "MIT Institute for Soldier Nanotechnologies (2002)",
    "University of Manchester — graphene body armour and military composites (2010– )": "University of Manchester — graphene body armour and military composites (2010)",
    "Fraunhofer IAPT — laser metal deposition for defence (Hamburg, 2017– )": "Fraunhofer IAPT — laser metal deposition for defence (Hamburg, 2017)",
    "Aleksandr Kogan — 'thisisyourdigitallife' (University of Cambridge, 2014–2015)": "Aleksandr Kogan — 'thisisyourdigitallife' (University of Cambridge, 2014–15)",
    "Uyghur-targeted face-recognition papers — academic-journal retractions (2018–2021)": "Uyghur-targeted face-recognition papers — academic-journal retractions (2018–21)",
    "UPenn GRASP Lab — autonomous drone swarms (Kumar lab, 2012– )": "UPenn GRASP Lab — autonomous drone swarms (Kumar lab, 2012)",
    "DARPA N3 academic grantees (2019– )": "DARPA N3 academic grantees (2019)",
    "Rafael Yuste & the NeuroRights Initiative (Columbia University, 2017– )": "Rafael Yuste & the NeuroRights Initiative (Columbia University, 2017)",
}


COUNTER_CASE_PAIRS = [
    (
        "RepRap — open-source 3D printing (University of Bath, 2005)",
        "PRIF Risk Assessment of 3D Firearms (Peace Research Institute Frankfurt, 2017)",
        "Open release is contrasted with an explicit assessment of proliferation pathways before or alongside dissemination.",
        Gate.G5,
    ),
    (
        "Peter Shor — polynomial-time factoring on a quantum computer (AT&T Bell Labs, 1994)",
        "Post-Quantum Cryptography Standardization (Positive Counter-case, NIST/Academia, 2016-Present)",
        "A future cryptographic threat is contrasted with early, coordinated development of protective replacements.",
        Gate.G3,
    ),
    (
        'Robotic "Dog" Weaponization (MIT Spin-off, 2020s)',
        "Pledge Against Weaponizing Robotics (Positive Counter-case, 2022)",
        "Unrestricted downstream adaptation is contrasted with public vendor boundaries and customer-use review.",
        Gate.G6,
    ),
]


def _validate_curated_inventory() -> None:
    titles = [case.title for case in CURATED_CASES]
    if len(set(titles)) != len(titles):
        raise ValueError("Curated case titles must be unique.")

    by_title = {case.title: case for case in CURATED_CASES}
    for old_title, new_title in PREVIOUS_CURATED_TITLES.items():
        if old_title in by_title or new_title not in by_title:
            raise ValueError(f"Invalid curated title rename: {old_title}")
    for case in CURATED_CASES:
        if case.main_pattern not in case.tagged_patterns:
            raise ValueError(f"Main pattern is not tagged: {case.title}")
        if case.main_gate not in case.tagged_gates:
            raise ValueError(f"Main gate is not tagged: {case.title}")
        if not case.references:
            raise ValueError(f"Missing source references: {case.title}")

    for harm_title, counter_title, _, _ in COUNTER_CASE_PAIRS:
        if by_title[harm_title].case_type is not CaseType.HARM:
            raise ValueError(f"Invalid harm-case link: {harm_title}")
        if by_title[counter_title].case_type is not CaseType.COUNTER_CASE:
            raise ValueError(f"Invalid counter-case link: {counter_title}")


async def seed() -> None:
    _validate_curated_inventory()
    engine = get_engine()

    async with AsyncSession(engine) as session:
        async with session.begin():
            # Demo fixtures are no longer seeded. Archive existing ones rather
            # than deleting them, so historical encounters still resolve.
            demo_cases = (
                await session.exec(select(Case).where(col(Case.title).like("Demo:%")))
            ).all()
            for demo_case in demo_cases:
                demo_case.status = CaseStatus.REVIEWED

            curated_by_title: dict[str, Case] = {}
            for curated in CURATED_CASES:
                case = await _seed_case(session, curated)
                curated_by_title[curated.title] = case

                # Preserve provisional cases and their historical encounters.
                # They must no longer appear in candidate or comparison sets.
                legacy_case = (
                    await session.exec(
                        select(Case).where(Case.title == curated.legacy_title)
                    )
                ).first()
                if legacy_case is not None:
                    legacy_case.status = CaseStatus.REVIEWED

            for harm_title, counter_title, contrast, lever in COUNTER_CASE_PAIRS:
                await _seed_counter_case_link(
                    session,
                    harm_case=curated_by_title[harm_title],
                    counter_case=curated_by_title[counter_title],
                    responsibility_posture_contrast=contrast,
                    gate_lever=lever,
                )

            renamed_cases = (
                await session.exec(
                    select(Case).where(col(Case.title).in_(PREVIOUS_CURATED_TITLES))
                )
            ).all()
            for renamed_case in renamed_cases:
                renamed_case.status = CaseStatus.REVIEWED

    print(f"Seeded {len(CURATED_CASES)} curated cases.")


if __name__ == "__main__":
    asyncio.run(seed())
