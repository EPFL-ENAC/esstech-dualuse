from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from api.models.base import timestamp_column, utc_now
from api.models.enums import AuthProvider, UserStatus, sa_enum


class User(SQLModel, table=True):
    """A real, authenticated identity, independent of any one login provider."""

    __tablename__ = "user"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    status: UserStatus = Field(
        default=UserStatus.ACTIVE,
        sa_column=Column(sa_enum(UserStatus), nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )


class AuthIdentity(SQLModel, table=True):
    """One login-provider identity linked to a User.

    provider_subject (Google's OIDC "sub" claim) is the join key.
    verified_email is informational only, never used to look up or merge
    identities: addresses change and get reused, sub does not. It is
    stored as Google reports it, regardless of Google's separate
    "email_verified" flag.
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
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
    last_login_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )


class LearningIdentity(SQLModel, table=True):
    """The stable learner_id a User is known by throughout the learning flow.

    Session.learner_id is deliberately not a foreign key to this table:
    the dev learner cookie mints learner_ids with no identity behind them.
    """

    __tablename__ = "learning_identity"

    learner_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", unique=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=timestamp_column(),
    )
