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
