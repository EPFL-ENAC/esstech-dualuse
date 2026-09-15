from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from api.models import Case, CaseEncounter, Commitment, ContrastEntry, Session
from api.models.enums import (
    CaseStatus,
    CaseType,
    ContrastType,
    Domain,
    Gate,
    Pattern,
    SessionMode,
    SessionRoute,
)


def _make_case() -> Case:
    return Case(
        title="Test Case",
        area="test-area",
        domain=Domain.CYBER_TECHNOLOGIES,
        case_type=CaseType.HARM,
        status=CaseStatus.PUBLISHED,
        narrative_until_crossroads="Narrative shown before the crossroads.",
        full_narrative="Full narrative revealed after commitment.",
        main_path_pattern=Pattern.A,
        main_path_gate=Gate.G1,
    )


def _make_session() -> Session:
    return Session(
        route=SessionRoute.STUDENT,
        mode=SessionMode.INDIVIDUAL,
        learner_id=uuid4(),
    )


async def test_case_encounter_capped_at_three_per_session(db_session):
    case = _make_case()
    session = _make_session()
    db_session.add(case)
    db_session.add(session)
    await db_session.flush()

    for sequence_no in (1, 2, 3):
        db_session.add(
            CaseEncounter(
                session_id=session.id, case_id=case.id, sequence_no=sequence_no
            )
        )
    await db_session.commit()

    db_session.add(CaseEncounter(session_id=session.id, case_id=case.id, sequence_no=4))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_case_encounter_sequence_no_unique_per_session(db_session):
    case = _make_case()
    session = _make_session()
    db_session.add(case)
    db_session.add(session)
    await db_session.flush()

    db_session.add(CaseEncounter(session_id=session.id, case_id=case.id, sequence_no=1))
    await db_session.commit()

    db_session.add(CaseEncounter(session_id=session.id, case_id=case.id, sequence_no=1))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_both_commitments_persist_after_a_revote(db_session):
    case = _make_case()
    session = _make_session()
    db_session.add(case)
    db_session.add(session)
    await db_session.flush()

    encounter = CaseEncounter(session_id=session.id, case_id=case.id, sequence_no=1)
    db_session.add(encounter)
    await db_session.flush()

    original = Commitment(
        case_encounter_id=encounter.id,
        sequence_no=1,
        pattern=Pattern.A,
        gate=Gate.G1,
        framing_answers={"why": "original reasoning"},
    )
    revised = Commitment(
        case_encounter_id=encounter.id,
        sequence_no=2,
        pattern=Pattern.B,
        gate=Gate.G2,
        framing_answers={"why": "revised after seeing the group distribution"},
    )
    db_session.add(original)
    db_session.add(revised)
    await db_session.commit()

    result = await db_session.exec(
        select(Commitment).where(Commitment.case_encounter_id == encounter.id)
    )
    commitments = result.all()

    assert len(commitments) == 2
    assert {c.sequence_no for c in commitments} == {1, 2}
    assert {c.pattern for c in commitments} == {Pattern.A, Pattern.B}


async def test_enum_column_stores_lowercase_value_not_member_name(db_session):
    """Regression guard for sa_enum()'s values_callable.

    SQLAlchemy's Enum type stores the Python member *name* by default (e.g.
    "HARM"), not its `.value` ("harm"). Reading back through the ORM would
    coerce either representation into CaseType.HARM and hide a regression,
    so this reads the raw column straight out of the database instead.
    """

    case = _make_case()
    db_session.add(case)
    await db_session.commit()

    result = await db_session.exec(text('SELECT case_type FROM "case"'))
    raw_case_type = result.one()[0]

    assert raw_case_type == "harm"
    assert raw_case_type == CaseType.HARM.value
    assert raw_case_type != CaseType.HARM.name


async def test_commitment_sequence_no_unique_per_encounter(db_session):
    case = _make_case()
    session = _make_session()
    db_session.add(case)
    db_session.add(session)
    await db_session.flush()

    encounter = CaseEncounter(session_id=session.id, case_id=case.id, sequence_no=1)
    db_session.add(encounter)
    await db_session.flush()

    db_session.add(
        Commitment(
            case_encounter_id=encounter.id,
            sequence_no=1,
            pattern=Pattern.A,
            gate=Gate.G1,
            framing_answers={},
        )
    )
    await db_session.commit()

    db_session.add(
        Commitment(
            case_encounter_id=encounter.id,
            sequence_no=1,
            pattern=Pattern.C,
            gate=Gate.G3,
            framing_answers={},
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_contrast_entry_unique_per_encounter(db_session):
    case = _make_case()
    session = _make_session()
    db_session.add(case)
    db_session.add(session)
    await db_session.flush()

    encounter = CaseEncounter(session_id=session.id, case_id=case.id, sequence_no=1)
    db_session.add(encounter)
    await db_session.flush()

    db_session.add(
        ContrastEntry(
            case_encounter_id=encounter.id,
            contrast_type=ContrastType.OPEN_AREA,
        )
    )
    await db_session.commit()

    db_session.add(
        ContrastEntry(
            case_encounter_id=encounter.id,
            contrast_type=ContrastType.OPEN_AREA,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
