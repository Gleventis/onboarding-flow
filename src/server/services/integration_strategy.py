"""
Module that holds the actual handler for the strategy pattern for the integrations
"""

import logging

from server.models.common import IntegrationResult, IntegrationStatus
from server.services.integrations.base import IntegrationClient
from server.services.integrations.bank_account import BankAccountClient
from server.services.integrations.credit import CreditClient
from server.services.integrations.identity import IdentityClient
from server.services.integrations.registry import RegistryClient
from server.services.integrations.sanctions import SanctionsClient

LOGGER = logging.getLogger(__name__)

INTEGRATION_CLIENTS: dict[str, IntegrationClient] = {
    "bank_account": BankAccountClient(),
    "credit": CreditClient(),
    "identity": IdentityClient(),
    "registry": RegistryClient(),
    "sanctions": SanctionsClient()
}

def handler(name: str, payload: dict, retries: int = 3) -> IntegrationResult:
    """
    the handler function for executing the appropriate client

    Args:
        name (str): the name of the integration
        payload (dict): the payload for the call function of the client
        retries (int, optional): number of retries. Defaults to 3.

    Returns:
        IntegrationResult: the result of the integration
    """
    client = INTEGRATION_CLIENTS.get(name)

    if not client:
        LOGGER.warning("no matching integration client, failing the process")
        return IntegrationResult(status=IntegrationStatus.failure, outcome="no matching integration client")

    for retry in range(retries):

        result = client.call(payload=payload)

        if result.status != IntegrationStatus.timeout:
            return result

        LOGGER.warning(f"Integration {name} timed out, retrying")

    return IntegrationResult(status=IntegrationStatus.failure, outcome="timeout")
