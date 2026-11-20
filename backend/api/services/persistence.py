from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)


async def insert_once(
    session: AsyncSession,
    record: T,
    find_existing: Callable[[], Awaitable[T | None]],
) -> tuple[T, bool]:
    """Flush `record`, or return the row that beat it to the UNIQUE constraint.

    Returns (row, created). The caller commits when created. A rollback
    expires every ORM object loaded earlier in the request, so callers must
    copy what they still need into plain values before calling this.
    """

    session.add(record)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        existing = await find_existing()
        if existing is None:
            raise
        return existing, False
    return record, True
