"""Reads of a researcher session's own records. Report and case-detail services
import these; the writing flows in researcher.py use them too."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import (
    ComparisonSet,
    ComparisonSetCase,
    ResearcherPrediction,
    SetContrastEntry,
    TechnologyIntake,
)
from api.models.enums import MappingStatus
from api.services.errors import ConflictError


async def find_technology_intake(
    session: AsyncSession, *, session_id: UUID
) -> TechnologyIntake | None:
    return (
        await session.exec(
            select(TechnologyIntake).where(TechnologyIntake.session_id == session_id)
        )
    ).first()


# The flow spec's "one clarification question, retry once".
MAX_TAG_ATTEMPTS = 2


def attempts_remaining(intake: TechnologyIntake) -> int:
    """How many /tag attempts this intake has left."""

    if intake.mapping_status == MappingStatus.MAPPED:
        return 0
    return max(0, MAX_TAG_ATTEMPTS - intake.clarification_count)


async def find_predictions(
    session: AsyncSession, *, session_id: UUID
) -> list[ResearcherPrediction]:
    """A session's submitted prediction, ordered by rank."""

    return list(
        (
            await session.exec(
                select(ResearcherPrediction)
                .where(ResearcherPrediction.session_id == session_id)
                .order_by(col(ResearcherPrediction.rank))
            )
        ).all()
    )


async def find_comparison_set(
    session: AsyncSession, *, session_id: UUID
) -> ComparisonSet | None:
    return (
        await session.exec(
            select(ComparisonSet).where(ComparisonSet.session_id == session_id)
        )
    ).first()


async def require_comparison_set(
    session: AsyncSession, *, session_id: UUID
) -> ComparisonSet:
    comparison_set = await find_comparison_set(session, session_id=session_id)
    if comparison_set is None:
        raise ConflictError("Session has no comparison set yet")
    return comparison_set


async def comparison_case_ids(session: AsyncSession, *, session_id: UUID) -> list[UUID]:
    comparison_set = await require_comparison_set(session, session_id=session_id)
    return list(
        (
            await session.exec(
                select(ComparisonSetCase.case_id).where(
                    ComparisonSetCase.comparison_set_id == comparison_set.id
                )
            )
        ).all()
    )


async def find_set_contrast_entry(
    session: AsyncSession, *, session_id: UUID
) -> SetContrastEntry | None:
    return (
        await session.exec(
            select(SetContrastEntry).where(SetContrastEntry.session_id == session_id)
        )
    ).first()
