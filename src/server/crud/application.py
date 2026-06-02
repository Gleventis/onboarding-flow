"""
holds the crud operations for the application
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.data_model import Application, Decision, Integration, Step
from server.models.api import AuditTrail, DecisionRecord, IntegrationRecord, StepRecord


def get_app_by_request_id(request_id: UUID, session: Session) -> Application | None:
    """
    queries the database using request_id to get the corresponding app

    Args:
        request_id (UUID): the app_id
        session (Session): db session

    Returns:
        Application: the retrieved applicatoin
    """
    return session.scalar(
        select(Application).where(
            Application.request_id == request_id
        )
    )


def get_app_by_token(token: str, session:Session) -> Application:
    """
    queries the database using token to get the corresponding app

    Args:
        token (str): the token
        session (Session): db session

    Returns:
        Application: the retrieved application
    """
    app = session.scalar(
        select(Application).where(
            Application.resume_token == token
            )
        )

    if not app:
        raise ValueError(f"no app found for {token=}")

    return app



def insert_app(app: Application, session: Session) -> None:
    """
    inserts the app to the database

    Args:
        app (Application): the app to be inserted
        session (Session): db session
    """
    session.add(app)


def get_app_audit_trail(app_id: UUID, session: Session) -> AuditTrail:
    """
    returns the full audit trail for a given app_id

    Args:
        app_id (UUID): the id of the app
        session (Session): db session

    Returns:
        AuditTrail: the audit trail
    """
    steps = session.scalars(
        select(Step).where(
            Step.application_id == app_id
        ).order_by(Step.created_at)
    ).all()


    integrations = session.scalars(
        select(Integration).where(
            Integration.application_id == app_id
        ).order_by(Integration.created_at)
    ).all()

    decision = session.scalar(
        select(Decision).where(
            Decision.application_id == app_id
        )
    )

    return AuditTrail(
        steps = [StepRecord.model_validate(step) for step in steps],
        integrations = [IntegrationRecord.model_validate(integration) for integration in integrations],
        decision = DecisionRecord.model_validate(decision) if decision else None
    )
