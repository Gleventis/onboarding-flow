"""
holds the crud operations for the decision
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.data_model import Decision


def insert_decision(decision: Decision, session: Session) -> None:
    """
    inserts the decision to the database

    Args:
        desicion (Decision): the desicion to be inserted
        session (Session): db session
    """
    session.add(decision)

def get_decision(app_id: UUID, session: Session) -> Decision | None:
    """
    returns the decision of a given app

    Args:
        app_id (UUID): the app id
        session (Session): the db session

    Returns:
        Decision | None: the decision row
    """
    return session.scalar(
        select(Decision).where(
            Decision.application_id == app_id
        )
    )
