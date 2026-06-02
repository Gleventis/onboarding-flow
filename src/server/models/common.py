"""
Shared enums and models
"""

from enum import StrEnum, auto

from pydantic import BaseModel


class Country(StrEnum):
    """
    Supported countries
    """

    sweden = auto()
    spain = auto()
    poland = auto()


class AccountType(StrEnum):
    """
    Supported account types
    """

    private = auto()
    business = auto()


class ApplicationStatus(StrEnum):
    """
    Possible status of an application
    """

    pending = auto()
    in_progress = auto()
    approved = auto()
    rejected = auto()
    manual_review = auto()
    expired = auto()
    abandoned = auto()


class StepStatus(StrEnum):
    """
    Possible status of a step
    """

    pending = auto()
    completed = auto()
    blocked = auto()
    terminated = auto()


class IntegrationStatus(StrEnum):
    """
    Possible status of an integration
    """

    pending = auto()
    success = auto()
    failure = auto()
    timeout = auto()


class DecisionOutcome(StrEnum):
    """
    Possible status of a final decision
    """

    approved = auto()
    rejected = auto()
    manual_review = auto()


class IntegrationResult(BaseModel):
    """
    The result of the mocked integration
    """

    status: IntegrationStatus
    outcome: str | None = None
    details: dict | None = None

