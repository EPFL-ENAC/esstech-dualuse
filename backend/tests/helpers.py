"""Shared test helpers (imported by test modules; fixtures live in conftest.py)."""

from datetime import datetime, timezone

from api.models import Case
from api.models.enums import CaseStatus, CaseType, Domain, Gate, Pattern


async def start_session(app_client, *, route: str | None = None) -> str:
    response = await app_client.post(
        "/sessions", json=None if route is None else {"route": route}
    )
    assert response.status_code == 201
    return response.json()["id"]


def instant(value: str) -> datetime:
    """Parse an API timestamp, tolerating SQLite's tz-less round-trip.

    Postgres returns timestamptz values tz-aware; SQLite drops the offset on
    read, so a freshly computed and a re-fetched value can serialize to
    different strings while denoting the same instant. Compare instants, not
    strings.
    """

    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def make_researcher_case(title: str, *, case_type: CaseType = CaseType.HARM) -> Case:
    return Case(
        title=title,
        area="fixture",
        domain=Domain.CYBER_TECHNOLOGIES,
        case_type=case_type,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="x",
        full_narrative="x",
        main_path_pattern=Pattern.A,
        main_path_gate=Gate.G1,
        source_references=[],
    )
