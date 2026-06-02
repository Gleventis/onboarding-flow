"""
the orchestrator brings everything together
"""
from datetime import datetime, timedelta, timezone
import logging
import secrets
from uuid import UUID
from sqlalchemy.orm import Session

from database.data_model import Application, Decision, Integration, Step
from server.core.registry import FLOWS, MAPPERS
from server.core.rules import build_cor
from server.core.steps import StepDefinition, get_step, next_step
from server.crud.application import get_app_audit_trail, insert_app
from server.crud.application import get_app_by_request_id, get_app_by_token
from server.crud.decision import get_decision, insert_decision
from server.crud.integration import create_integration_record, read_all_integ_results
from server.crud.step import get_step_by_app_and_name, insert_step
from server.models.api import AuditTrail, CreateAppResponse, DecisionRecord, ProgressResponse, SubmitStepResponse
from server.models.common import AccountType, Country, IntegrationResult
from server.config import settings
from server.services.integration_strategy import handler


LOGGER = logging.getLogger(__name__)

def create_app(country: Country, account_type: AccountType, request_id: UUID, session: Session) -> CreateAppResponse:
    """
    Creates the application for a (country, account_type) tuple

    Args:
        country (Country): selected country
        account_type (AccountType): selected account type(private or business)
        request_id (UUID): the request id to check for existing applications in the database
        session (Session): db session

    Returns:
        CreateAppResponse: pydantic model with app_id, resume_token, current step fields
    """

    flow = FLOWS.get((country, account_type))

    if not flow:
        raise ValueError(f"the combination of {country, account_type} is currently not available")

    existing_app:Application = get_app_by_request_id(request_id=request_id, session=session)

    if existing_app:

        LOGGER.info(f"found existing app with current step {existing_app.current_step_id}")

        return CreateAppResponse(app_id=existing_app.id, resume_token=existing_app.resume_token,
                                 current_step=existing_app.current_step_id)

    LOGGER.info(f"creating application for ({country}, {account_type})")

    now = datetime.now(tz=timezone.utc)
    token = secrets.token_urlsafe()
    expires_at = now + timedelta(seconds=settings.token_expiry_seconds)
    # create app record
    app = Application(country=country, account_type=account_type, current_step_id=flow[0].name,
                      request_id=request_id, resume_token=token, token_expiration_date=expires_at,
                      status="in_progress")

    insert_app(app=app, session=session)

    session.flush()

    return CreateAppResponse(app_id=app.id, resume_token=token, current_step=flow[0].name)

def submit_step(step_name: str, form_payload: dict, token: str, session: Session) -> SubmitStepResponse:
    """
    submits form payload for a step

    Args:
        step_name (str): name of the step
        form_payload (dict): the form payload
        token (str): resume token
        session (Session): the session

    Returns:
        SubmitStepResponse: pydantic model with step_status, current_step fields
    """
    app: Application = get_app_by_token(token=token, session=session)

    existing_step: Step | None = get_step_by_app_and_name(app_id = app.id, step_name = step_name, session=session)

    if existing_step:
        return SubmitStepResponse(step_status=existing_step.status, current_step=app.current_step_id)

    flow = FLOWS.get((app.country, app.account_type))

    mappers = MAPPERS.get((app.country, app.account_type), {})

    if not is_active(app=app):
        raise ValueError(f"no active application with {token=}")

    step = get_step(steps=flow, name=step_name)

    if step_name != app.current_step_id:
        raise ValueError(f"expected step {app.current_step_id}, got {step_name}")

    LOGGER.debug(f"submitting {step=} for app {app.id}")

    validated_step: StepDefinition = step.form_schema(**form_payload)

    # external integrations
    integration_results:list[IntegrationResult] = []

    for integration in step.integrations:

        mapper = mappers.get(integration)

        payload = mapper(validated_step.model_dump()) if mapper else validated_step.model_dump()

        integration_result:IntegrationResult = handler(name=integration, payload=payload)

        LOGGER.info(f"ran {integration=} with result {integration_result.status}")

        integration_results.append(integration_result)

        integration_record = Integration(
            application_id=app.id,
            step_name=step_name,
            integration_name=integration,
            request_payload=form_payload,
            response_payload=integration_result.model_dump(),
            status=integration_result.status
        )

        create_integration_record(integration=integration_record, session=session)

    # gates
    step_status: str = step.gate(integration_results)

    LOGGER.info(f"step {step_name} had result {step_status}")

    step_record = Step(
        application_id=app.id,
        step_name=step.name,
        form_data=form_payload,
        status=step_status
    )

    insert_step(step=step_record, session=session)

    if step_status == "completed":
        following_step: StepDefinition | None = next_step(steps=flow, current=step.name)

        if following_step:
            app.current_step_id = following_step.name

        else:
            app.current_step_id = None

            chain = build_cor()

            all_integ_results = read_all_integ_results(app_id=app.id, session=session)

            decision, reasons = chain.handle(results=all_integ_results)

            LOGGER.info(f"decision outcome {decision} with reasons {reasons}")

            app.status = decision

            final_decision = Decision(application_id=app.id ,outcome=decision, reasons=reasons)

            insert_decision(decision=final_decision, session=session)

        app.token_expiration_date = datetime.now(tz=timezone.utc) + timedelta(seconds=settings.token_expiry_seconds)

    elif step_status == "terminated":

        LOGGER.warning(f"step {step_name} terminated")

        app.status = "rejected"
        app.current_step_id = None

        final_decision = Decision(application_id=app.id, outcome="rejected",
                                  reasons=[f"terminated at step: {step_name}"])
        insert_decision(decision=final_decision, session=session)


    return SubmitStepResponse(step_status=step_status, current_step=app.current_step_id)


def is_active(app: Application) -> bool:
    """
    checks if current app is active

    Args:
        app (Application): the app to check the status for

    Returns:
        bool: if the current app is active or not
    """
    now: datetime = datetime.now(tz=timezone.utc).replace(tzinfo=None)

    if app.token_expiration_date < now:

        LOGGER.debug(f"{app.id} has expired")

        app.status = "expired"

    return app.status in ("pending", "in_progress")


def get_progress(token: str, session: Session) -> ProgressResponse:
    """
    function for returning the progress of an application

    Args:
        token (str): the resume token
        session (Session): the session

    Returns:
        GetProgressResponse: pydantic model with total_steps, completed_steps, current_step, remaining fields
    """
    existing_app: Application = get_app_by_token(token=token, session=session)

    if not is_active(app=existing_app):

        LOGGER.info("progress report requested for in-active application")

        return ProgressResponse()

    flow = FLOWS.get((Country(existing_app.country), AccountType(existing_app.account_type)))

    all_steps = [step.name for step in flow]

    current_step_index = all_steps.index(existing_app.current_step_id)

    completed_steps = all_steps[:current_step_index]

    return ProgressResponse(total_steps=len(flow),
                            completed_steps=completed_steps,
                            current_step=existing_app.current_step_id,
                            remaining_steps=all_steps[current_step_index:])


def abandon_application(token: str, session: Session) -> Application:
    """
    changes the status of the app to abandoned

    Args:
        token (str): the token that we get the app with
        session (Session): the session

    Returns:
        Application: the abandoned application
    """
    app_to_modify: Application = get_app_by_token(token=token, session=session)

    LOGGER.debug(f"abandoning app with id {app_to_modify.id}")

    app_to_modify.status = "abandoned"

    app_to_modify.updated_at = datetime.now(tz=timezone.utc)

    LOGGER.info(f"abandoned app with token {token}")

    return app_to_modify


def read_decision(token: str, session: Session) -> DecisionRecord | None:
    """
    function that returns a decision given a token

    Args:
        token (str): the resume token
        session (Session): the session

    Returns:
        DecisionRecord | None: a decision if one exists
    """
    app: Application = get_app_by_token(token=token, session=session)

    decision: Decision | None = get_decision(app_id=app.id, session=session)

    if not decision:
        return None

    return DecisionRecord.model_validate(decision)


def read_audit(token: str, session: Session) -> AuditTrail:
    """
    function that returns an audit trail given a token

    Args:
        token (str): the resumet token
        session (Session): db session

    Returns:
        AuditTrail: the audit trail
    """
    app: Application = get_app_by_token(token=token, session=session)

    audit_trail: AuditTrail = get_app_audit_trail(app_id=app.id, session=session)

    return audit_trail

