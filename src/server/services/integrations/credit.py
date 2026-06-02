"""
Holds the integration for the credit
"""
import logging
from pydantic import BaseModel, ValidationError

from server.models.common import IntegrationResult, IntegrationStatus

class CreditPayload(BaseModel):
    """
    validation of payload for credit client
    """
    income: float
    debt: int


class CreditClient:
    """
    Implementation of the IntegrationClient for the credit integration
    """
    def call(self, payload: dict) -> IntegrationResult:
        """
        Concrete implementation of the call function for the credit client
        Args:
            payload (dict): payload to the client

        Returns:
            IntegrationResult: the integration result
        """
        try:
            validated = CreditPayload(**payload)
        except ValidationError as error:
            logging.warning(f"credit payload validation failed {error}")
            return IntegrationResult(status=IntegrationStatus.failure, outcome=None)

        score: int = validated.income - validated.debt # crude calculation for the sake of this exercise

        if score <= 49:
            return IntegrationResult(status=IntegrationStatus.success, outcome="below_threshold",
                                     details={"score": score, "debt_flags": [],
                                              "disposable_income": validated.income,
                                              "decision_reason": ""})
        else:
            return IntegrationResult(status=IntegrationStatus.success, outcome="above_threshold",
                                     details={"score": score, "debt_flags": [],
                                              "disposable_income": validated.income,
                                              "decision_reason": ""})
