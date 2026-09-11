"""Endpoint tests for the post-reveal contrast reflection (M5).

The API and these tests share one database session (see the `app_client`
fixture), so fixture rows must be committed before any API call.
"""

from uuid import uuid4

import pytest
from sqlmodel import select

from api.models import Case, ContrastEntry, CounterCaseLink
from api.models.enums import CaseStatus, CaseType, Gate, Pattern


def _make_case(
    title: str = "Harm Case",
    *,
    case_type: CaseType = CaseType.HARM,
) -> Case:
    return Case(
        title=title,
        area="area-1",
        case_type=case_type,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="Narrative before the crossroads.",
        full_narrative="Full narrative.",
        main_path_pattern=Pattern.A,
        main_path_gate=Gate.G1,
        source_references=[],
    )


async def _start_session(app_client) -> str:
    response = await app_client.post("/sessions")
    assert response.status_code == 201
    return response.json()["id"]


async def _encounter_for(app_client, db_session, case: Case) -> str:
    """Persist `case`, start a session, select it, and return the encounter id."""

    db_session.add(case)
    await db_session.commit()

    session_id = await _start_session(app_client)
    response = await app_client.post(
        f"/sessions/{session_id}/encounters", json={"case_id": str(case.id)}
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _link_counter_case(db_session, *, harm_case: Case) -> CounterCaseLink:
    counter_case = Case(
        title="Counter Case",
        area=harm_case.area,
        case_type=CaseType.COUNTER_CASE,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="Counter-case narrative.",
        full_narrative="Counter-case full narrative.",
        main_path_pattern=Pattern.B,
        main_path_gate=Gate.G2,
        source_references=[],
    )
    db_session.add(counter_case)
    await db_session.flush()

    link = CounterCaseLink(
        harm_case_id=harm_case.id,
        counter_case_id=counter_case.id,
        responsibility_posture_contrast="The counter-case redistributes responsibility upstream.",
        gate_lever=Gate.G2,
    )
    db_session.add(link)
    await db_session.commit()
    return link


async def test_counter_case_lookup_reports_none_when_no_link_exists(
    app_client, db_session
):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)

    response = await app_client.get(f"/encounters/{encounter_id}/counter-case")

    assert response.status_code == 200
    assert response.json() == {"has_counter_case": False, "counter_case": None}


async def test_counter_case_lookup_reports_the_linked_counter_case(
    app_client, db_session
):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)
    link = await _link_counter_case(db_session, harm_case=case)

    response = await app_client.get(f"/encounters/{encounter_id}/counter-case")

    assert response.status_code == 200
    body = response.json()
    assert body["has_counter_case"] is True
    assert body["counter_case"] == {
        "counter_case_id": str(link.counter_case_id),
        "gate_lever": Gate.G2.value,
        "responsibility_posture_contrast": link.responsibility_posture_contrast,
    }


@pytest.mark.parametrize("learner_response", [None, "", "   "])
async def test_twin_counter_case_requires_a_non_empty_response(
    app_client, db_session, learner_response
):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)
    await _link_counter_case(db_session, harm_case=case)

    response = await app_client.post(
        f"/encounters/{encounter_id}/contrast",
        json={"learner_response": learner_response},
    )

    assert response.status_code == 422

    entries = (await db_session.exec(select(ContrastEntry))).all()
    assert entries == []


async def test_twin_counter_case_stores_the_response(app_client, db_session):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)
    link = await _link_counter_case(db_session, harm_case=case)

    response = await app_client.post(
        f"/encounters/{encounter_id}/contrast",
        json={"learner_response": "  The team that chose the release path.  "},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contrast_type"] == "twin_counter_case"
    assert body["counter_case_id"] == str(link.counter_case_id)
    assert body["learner_response"] == "The team that chose the release path."


async def test_open_area_ignores_any_client_supplied_response(app_client, db_session):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)

    response = await app_client.post(
        f"/encounters/{encounter_id}/contrast",
        json={"learner_response": "text sent anyway"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contrast_type"] == "open_area"
    assert body["counter_case_id"] is None
    # The client's text is discarded, not merely ignored on read: the stored
    # row itself must never carry input for a branch that asked nothing.
    assert body["learner_response"] is None


async def test_contrast_submission_twice_returns_the_identical_entry(
    app_client, db_session
):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)
    await _link_counter_case(db_session, harm_case=case)

    first = await app_client.post(
        f"/encounters/{encounter_id}/contrast",
        json={"learner_response": "First answer."},
    )
    second = await app_client.post(
        f"/encounters/{encounter_id}/contrast",
        json={"learner_response": "A different answer that must not overwrite it."},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["contrast_entry_id"] == second.json()["contrast_entry_id"]
    assert second.json()["learner_response"] == "First answer."

    entries = (await db_session.exec(select(ContrastEntry))).all()
    assert len(entries) == 1


async def test_another_learners_encounter_is_not_found(app_client, db_session, learner):
    case = _make_case()
    encounter_id = await _encounter_for(app_client, db_session, case)

    learner["id"] = uuid4()
    counter_case = await app_client.get(f"/encounters/{encounter_id}/counter-case")
    contrast = await app_client.post(
        f"/encounters/{encounter_id}/contrast", json={"learner_response": "x"}
    )

    assert counter_case.status_code == 404
    assert contrast.status_code == 404
