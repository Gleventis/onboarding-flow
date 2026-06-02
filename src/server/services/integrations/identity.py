"""
Holds the integration for the identity
"""
import logging
from pydantic import BaseModel, ValidationError

from server.models.common import IntegrationResult, IntegrationStatus

class IdentityPayload(BaseModel):
    """
    validation of payload for identity client
    """
    personal_id: str


class IdentityClient:
    """
    Implementation of the IntegrationClient for the identity integration
    """
    def call(self, payload: dict) -> IntegrationResult:
        """
        Concrete implementation of the call function for the identity client
        Args:
            payload (dict): payload to the client

        Returns:
            IntegrationResult: the integration result
        """
        try:
            validated = IdentityPayload(**payload)
        except ValidationError as error:
            logging.warning(f"identity payload failed: {error}")
            return IntegrationResult(status=IntegrationStatus.failure, outcome=None)

        if validated.personal_id.endswith("0"):
            return IntegrationResult(status=IntegrationStatus.success, outcome="expired_id")

        if validated.personal_id.endswith("1"):
            return IntegrationResult(status=IntegrationStatus.success, outcome="document_mismatch")

        if validated.personal_id.endswith("2"):
            return IntegrationResult(status=IntegrationStatus.success, outcome="identity_manual_review")

        return IntegrationResult(status=IntegrationStatus.success, outcome="verified")
