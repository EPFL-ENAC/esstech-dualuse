from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from api.models.enums import AuthProvider, UserStatus, sa_enum


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    """A real, authenticated identity, independent of any one login provider."""

    __tablename__ = "user"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    status: UserStatus = Field(
        default=UserStatus.ACTIVE,
        sa_column=Column(sa_enum(UserStatus), nullable=False),
    )
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class AuthIdentity(SQLModel, table=True):
    """One login-provider identity linked to a User.

    provider_subject is the provider's own stable identifier (Google's
    OIDC "sub" claim) -- the real join key. verified_email is
    informational only, never used to look up or merge identities:
    addresses change and get reused, sub does not.
    """

    __tablename__ = "auth_identity"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_subject", name="uq_auth_identity_provider_subject"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    provider: AuthProvider = Field(
        sa_column=Column(sa_enum(AuthProvider), nullable=False)
    )
    provider_subject: str
    verified_email: str
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    last_login_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class LearningIdentity(SQLModel, table=True):
    """The stable learner_id a User is known by throughout the learning flow.

    This is the same value Session.learner_id has always stored
    (api/models/session.py), now backed by a real identity instead of a
    per-browser dev cookie. Session.learner_id is deliberately not a
    foreign key to this table yet: the dev cookie has already minted
    learner_ids with no real identity behind them, and forcing the FK
    now would mean either fabricating placeholder identities for them or
    adding an unvalidated constraint. A later migration can add the FK
    once real (not dev-cookie) data is what populates this table.
    """

    __tablename__ = "learning_identity"

    learner_id: UUID = Field(default_factory=uuid4, primary_key=True)
    # 1:1: one LearningIdentity per User, the same shape as
    # SessionIntake's 1:1-per-session unique FK (api/models/intake.py).
    user_id: UUID = Field(foreign_key="user.id", unique=True)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
