"""
Holds the base protocol class for the strategy pattern
"""
from typing import Protocol

from server.models.common import IntegrationResult

class IntegrationClient(Protocol):
    """
    protocol class that each integration will provide a concrete implementation for
    """
    def call(self, payload: dict) -> IntegrationResult:
        """
        calls the integration with payload

        Args:
            payload (dict): the payload for the integration call

        Returns:
            IntegrationResult: the result of the integration
        """
