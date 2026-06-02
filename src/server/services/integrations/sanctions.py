"""
Holds the integration for the sanctions
"""
import logging
from pydantic import BaseModel, ValidationError

from server.models.common import IntegrationResult, IntegrationStatus

class SanctionsPayload(BaseModel):
    """
    validation of payload for sanctions client
    """
    name: str

class SanctionsClient:
    """
    Implementation of the IntegrationClient for the sanctions integration
    """
    def call(self, payload: dict) -> IntegrationResult:
        """
        Concrete implementation of the call function for the sanctions client
        Args:
            payload (dict): payload to the client

        Returns:
            IntegrationResult: the integration result
        """

        try:
            validated = SanctionsPayload(**payload)
        except ValidationError as error:
            logging.warning(f"sanctions payload validation failed {error}")
            return IntegrationResult(status=IntegrationStatus.failure, outcome=None)

        if validated.name.startswith("confirmed"):
            return IntegrationResult(status=IntegrationStatus.success, outcome="confirmed_hit")

        if validated.name.startswith("possible"):
            return IntegrationResult(status=IntegrationStatus.success, outcome="possible_hit")

        return IntegrationResult(status=IntegrationStatus.success, outcome="no_hit")