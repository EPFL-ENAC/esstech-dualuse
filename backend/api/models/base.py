from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp_column(*, nullable: bool = False, **kwargs: Any) -> Column:
    return Column(DateTime(timezone=True), nullable=nullable, **kwargs)
