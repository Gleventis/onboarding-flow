"""
holds the crud operations for the step
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.data_model import Step


def insert_step(step: Step, session: Session) -> None:
    """
    inserts the step to the database

    Args:
        step (Step): the step to be inserted
        session (Session): db session
    """
    session.add(step)

def get_step_by_app_and_name(app_id: str, step_name: str, session: Session) -> Step | None:
    """
    queries step table to find existing step for given app

    Args:
        app_id (str): the application id
        step_name (str): the step name
        session (Session): db session

    Returns:
        Step | None: the step record if it exists, none otherwise
    """
    return session.scalar(
        select(Step).where(
            Step.application_id == app_id,
            Step.step_name == step_name
        )
    )