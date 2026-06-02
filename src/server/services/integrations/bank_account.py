"""
Holds the integration for the bank account
"""
import logging
from pydantic import BaseModel, ValidationError

from server.models.common import IntegrationResult, IntegrationStatus

class BankAccountPayload(BaseModel):
    """
    validation of payload for bank account client
    """
    iban: str
    account_name: str


class BankAccountClient:
    """
    Implementation of the IntegrationClient for the bank account integration
    """
    def call(self, payload: dict) -> IntegrationResult:
        """
        Concrete implementation of the call function for the bank account client
        Args:
            payload (dict): payload to the client

        Returns:
            IntegrationResult: the integration result
        """
        try:
            validated = BankAccountPayload(**payload)
        except ValidationError as error:
            logging.warning(f"bank account payload validation failed {error}")
            return IntegrationResult(status=IntegrationStatus.failure, outcome=None)

        if validated.iban.startswith("name_mismatch"):
            return IntegrationResult(status=IntegrationStatus.success, outcome="name_mismatch")

        if validated.iban.startswith("wrong_iban"):
            return IntegrationResult(status=IntegrationStatus.success, outcome="wrong_iban")

        if validated.iban.startswith("unreachable"):
            return IntegrationResult(status=IntegrationStatus.timeout, outcome="unreachable")

        return IntegrationResult(status=IntegrationStatus.success, outcome="iban_verified")