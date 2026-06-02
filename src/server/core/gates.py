"""
Module that holds the gate functions
"""

from server.models.common import IntegrationResult, IntegrationStatus, StepStatus

# Immediately terminated
REJECTION_OUTCOMES = {"failed", "confirmed_hit", "inactive"}


def pass_through(results: list[IntegrationResult]) -> StepStatus:
    """
    Allows the flow to proceed unconditionally.

    Args:
        results (list): list of Integration Result models

    Returns:
       (StepStatus): StepStatus.completed unconditionally.
    """
    return StepStatus.completed


def block_on_error(results: list[IntegrationResult]) -> StepStatus:
    """
    Blocks the step if any integration had a technical failure.

    Args:
        results(list[IntegrationResult]): list of Integration Result models

    Returns:
        (StepStatus): StepStatus.blocked if any result has failure/timeout status, StepStatus.completed otherwise.
    """
    failure_statuses = {IntegrationStatus.failure, IntegrationStatus.timeout}
    for result in results:
        if result.status in failure_statuses:
            return StepStatus.blocked
    return StepStatus.completed


def terminate_on_rejection(results: list[IntegrationResult]) -> StepStatus:
    """
    Terminates the application if any integration returned a rejection outcome.

    Args:
        results (list[IntegrationResult]): Integration result models

    Returns:
        (StepStatus): StepStatus.terminated if any result outcome is a rejection indicator,
        StepStatus.blocked if any integration failed/timed out, StepStatus.completed otherwise.
    """
    for result in results:
        if result.outcome in REJECTION_OUTCOMES:
            return StepStatus.terminated
    return block_on_error(results)
