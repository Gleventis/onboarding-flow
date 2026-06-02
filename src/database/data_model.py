"""
ORM models for the onboarding flow database
"""

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, JSON, Text, Uuid, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.meta import Model

application_status_enum = Enum(
    "pending",
    "in_progress",
    "approved",
    "rejected",
    "manual_review",
    "expired",
    "abandoned",
    name="application_status",
)

step_status_enum = Enum(
    "pending",
    "completed",
    "blocked",
    "terminated",
    name="step_status",
)

integration_status_enum = Enum(
    "pending",
    "success",
    "failure",
    "timeout",
    name="integration_status",
)

decision_outcome_enum = Enum(
    "approved",
    "rejected",
    "manual_review",
    name="decision_outcome",
)


class Application(Model):
    """
    Table for applications
    """

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))

    country: Mapped[str] = mapped_column(Text, nullable=False)

    account_type: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(application_status_enum, nullable=False, server_default="pending")

    current_step_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, unique=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    resume_token: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    token_expiration_date: Mapped[datetime] = mapped_column(nullable=False)

    # 1-N relationships
    steps: Mapped[list["Step"]] = relationship(
        back_populates="application"
    )
    integrations: Mapped[list["Integration"]] = relationship(
        back_populates="application"
    )
    # 1-1 relationship
    decision: Mapped["Decision | None"] = relationship(
        back_populates="application", uselist=False
    )


class Step(Model):
    """
    Table for steps
    """

    __tablename__ = "steps"

    # Unique constraint on app_id and step_name to avoid same step twice for same app
    __table_args__ = ( UniqueConstraint('application_id', 'step_name', name='uix_application_step'),)

    id: Mapped[int] = mapped_column(primary_key=True)

    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), index=True)

    step_name: Mapped[str] = mapped_column(Text, nullable=False)

    form_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[str] = mapped_column(step_status_enum, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )

    # N-1 relationship
    application: Mapped["Application"] = relationship(back_populates="steps")


class Integration(Model):
    """
    Table for integrations
    """

    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(primary_key=True)

    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), index=True)

    step_name: Mapped[str] = mapped_column(Text, nullable=False)

    integration_name: Mapped[str] = mapped_column(Text, nullable=False)

    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(integration_status_enum, nullable=False)

    duration_ms: Mapped[int | None] = mapped_column(nullable=True)

    attempt: Mapped[int] = mapped_column(nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )

    # N-1 relationship
    application: Mapped["Application"] = relationship(
        back_populates="integrations"
    )


class Decision(Model):
    """
    Table for the decisions
    """

    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)

    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), index=True, unique=True)

    outcome: Mapped[str] = mapped_column(decision_outcome_enum, nullable=False)

    reasons: Mapped[list] = mapped_column(JSON, nullable=False)

    decided_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )

    # 1-1 relationship
    application: Mapped["Application"] = relationship(back_populates="decision")
