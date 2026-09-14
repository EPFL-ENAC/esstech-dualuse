from enum import Enum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=Enum)


def sa_enum(enum_cls: type[E]) -> SAEnum:
    """Build a VARCHAR+CHECK column type storing enum `.value`s (not `.name`s).

    SQLAlchemy's `Enum` stores member *names* by default, which would put
    "HARM" in the database for `CaseType.HARM = "harm"`. `values_callable`
    makes it store `.value` instead, matching what the API and any direct
    SQL against the database will actually see.
    """

    return SAEnum(
        enum_cls,
        native_enum=False,
        values_callable=lambda cls: [member.value for member in cls],
    )


class CaseType(str, Enum):
    """Whether a case presents the harmful path or the counter-case contrast."""

    HARM = "harm"
    COUNTER_CASE = "counter_case"


class CaseStatus(str, Enum):
    """Editorial status of a case. Only PUBLISHED cases are ever offered to users."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    PUBLISHED = "published"


class SessionRoute(str, Enum):
    """Which top-level path a session was started through."""

    STUDENT = "student"
    RESEARCHER = "researcher"


class SessionMode(str, Enum):
    """How a session is run. Only INDIVIDUAL is used for now."""

    INDIVIDUAL = "individual"
    GROUP = "group"
    LECTURE = "lecture"


class MatchResult(str, Enum):
    """How a learner's commitment compares to the case's main path."""

    MATCH = "match"
    PARTIAL_MATCH = "partial_match"
    MISMATCH = "mismatch"


class Pattern(str, Enum):
    """The 16 fixed dual-use reasoning patterns."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"  # noqa: E741 -- matches the domain's own pattern label, not a stray variable
    J = "J"
    K = "K"
    L = "L"  # noqa: E741 -- matches the domain's own pattern label, not a stray variable
    M = "M"
    N = "N"
    O = "O"  # noqa: E741 -- matches the domain's own pattern label, not a stray variable
    P = "P"


class Gate(str, Enum):
    """The 6 fixed decision gates."""

    G1 = "G1"
    G2 = "G2"
    G3 = "G3"
    G4 = "G4"
    G5 = "G5"
    G6 = "G6"


class ScaffoldingDepth(str, Enum):
    """How much support a learner is judged to need after M0 intake.

    PLACEHOLDER. These three levels and the rule that picks between them
    (api/content/intake_key.py) stand in for a real pedagogical model that has
    not been designed yet. Nothing reads this value: it is persisted for a
    later milestone, deliberately not wired to hints, difficulty, or anything
    else. Expect the member set itself to change once the real model exists.
    """

    HIGH = "high"
    STANDARD = "standard"
    LOW = "low"


class ContrastType(str, Enum):
    """Which post-reveal reflection branch an encounter received.

    Derived server-side from whether the encounter's case has a linked
    counter-case, never supplied by the client.
    """

    TWIN_COUNTER_CASE = "twin_counter_case"
    OPEN_AREA = "open_area"


class Domain(str, Enum):
    """The technology domain a researcher's project belongs to.

    Part of the Function/Form/Domain taxonomy confirmed by the team
    (Louis). Values are the exact display strings, not codes -- matched
    and rendered verbatim, so do not alter them.
    """

    MATERIAL_SCIENCE = "Material Science"
    ADVANCED_MANUFACTURING = "Advanced Manufacturing / 3D Printing"
    SEMICONDUCTORS_NANOTECH = "Semiconductors and Nanotechnology"
    ARTIFICIAL_INTELLIGENCE = "Artificial Intelligence"
    CYBER_TECHNOLOGIES = "Cyber Technologies"
    QUANTUM_TECHNOLOGY = "Quantum Technology"
    ROBOTICS_AUTONOMOUS = "Robotics & Autonomous Systems"
    NEUROTECHNOLOGY = "Neurotechnology"
    BIOCHEMISTRY = "Biochemistry"


class Function(str, Enum):
    """What a technology does.

    The Function facet of the Function/Form/Domain taxonomy used to match
    a researcher's project against the case corpus.
    """

    SENSING = "sensing"
    GENERATING = "generating"
    CONTROLLING = "controlling"
    PREDICTING = "predicting"
    EDITING = "editing"
    OPTIMIZING = "optimizing"
    FABRICATING = "fabricating"
    COMPUTING = "computing"


class Form(str, Enum):
    """What shape a technology takes.

    The Form facet of the Function/Form/Domain taxonomy.
    """

    PLATFORM = "platform"
    MODEL = "model"
    DATASET = "dataset"
    PROTOCOL = "protocol"
    DEVICE = "device"
    INFRASTRUCTURE = "infrastructure"
    MATERIAL = "material"
    METHOD = "method"


class MappingStatus(str, Enum):
    """How completely a TechnologyIntake's Function/Form/Domain facets are
    filled in.

    MAPPED: domain, functions, and forms are all present. PARTIAL: at least
    one is present, but not all three. UNMAPPED: none are present yet.
    """

    MAPPED = "mapped"
    PARTIAL = "partial"
    UNMAPPED = "unmapped"
