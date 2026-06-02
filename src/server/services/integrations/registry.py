"""
Holds the integration for the registry
"""
import logging
from pydantic import BaseModel, ValidationError

from server.models.common import IntegrationResult, IntegrationStatus

class RegistryPayload(BaseModel):
    """
    validation of payload for registry client
    """
    registration_number: str
    country: str

class RegistryClient:
    """
    Implementation of the IntegrationClient for the registry integration
    """
    def call(self, payload: dict) -> IntegrationResult:
        """
        Concrete implementation of the call function for the registry client
        Args:
            payload (dict): payload to the client

        Returns:
            IntegrationResult: the integration result
        """

        try:
            validated = RegistryPayload(**payload)
        except ValidationError as error:
            logging.warning(f"registry payload validation failed {error}")
            return IntegrationResult(status=IntegrationStatus.failure, outcome=None)

        if validated.registration_number.startswith("0"):
                return IntegrationResult(status=IntegrationStatus.success, outcome="dissolved")

        if validated.registration_number.startswith("1"):
                return IntegrationResult(status=IntegrationStatus.success, outcome="unknown_representative")

        if validated.registration_number.startswith("2"):
            return IntegrationResult(status=IntegrationStatus.success, outcome="missing_ubo")

        return IntegrationResult(status=IntegrationStatus.success, outcome="active_company")
