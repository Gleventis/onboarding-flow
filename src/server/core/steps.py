"""
step definitions for the onboarding flow
"""

from dataclasses import dataclass, field
from typing import Callable

from pydantic import BaseModel

from server.core.gates import pass_through
from server.models.common import StepStatus

GateFunction = Callable[[list[dict]], StepStatus]

@dataclass
class StepDefinition:
    """
    Single step
    """

    name: str
    form_schema: type[BaseModel]
    integrations: list[str] = field(default_factory=list)
    gate: GateFunction = pass_through


def get_step(steps: list[StepDefinition], name: str) -> StepDefinition | None:
    """
    Find a step given its name

    Args:
        steps (list[StepDefinition]): step list
        name (str): step name to find

    Returns:
        (StepDefinition | None): matching step or None
    """
    return next((step for step in steps if step.name == name), None)


def next_step(steps: list[StepDefinition], current: str) -> StepDefinition | None:
    """
    Get the next step

    Args:
        steps (list[StepDefinition]): step list
        current (str): current step name

    Returns:
        (StepDefinition | None): next step or None if last
    """
    for index, step in enumerate(steps, start=1):
        if step.name == current and index < len(steps):
            return steps[index]
    return None
