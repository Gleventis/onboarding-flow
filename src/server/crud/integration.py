"""
holds the crud operations for the integration
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.data_model import Integration
from server.models.common import IntegrationResult


def create_integration_record(integration: Integration, session: Session) -> None:
    """
    inserts the integration to the database

    Args:
        integration (Integration): the integration to be inserted
        session (Session): db session
    """
    session.add(integration)

def read_all_integ_results(app_id: UUID, session: Session) -> list[IntegrationResult]:
    """
    queries the database and returns all the integrations that belong to a given app

    Args:
        app_id (UUID): the app id
        session (Session): db session

    Returns:
        list[IntegrationResult]: list of integration results
    """
    records = session.scalars(
        select(Integration).where(
            Integration.application_id == app_id
        )
    ).all()
    return [IntegrationResult(**record.response_payload) for record in records]
