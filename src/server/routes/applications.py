"""
application routes
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from server.database_handler import get_onboarding_db
from server.models.api import AuditTrail, CreateAppRequest, CreateAppResponse, DecisionRecord, ProgressResponse, SubmitStepResponse
from server.services.orchestrator import abandon_application, create_app, read_audit, read_decision, submit_step, get_progress as read_progress

router = APIRouter(prefix="/application", tags=["Applications"])

@router.post("/create", response_model=CreateAppResponse, status_code=status.HTTP_200_OK)
def create_application(app_request: CreateAppRequest, session: Session = Depends(get_onboarding_db)):
    """
    endpoint that triggers the creation of an app

    Args:
        app_request (CreateAppRequest): the body of the request
        session (Session, optional): the db session. Defaults to Depends(get_onboarding_db)
    """
    try:
        app_response = create_app(country=app_request.country, account_type=app_request.account_type,
                                request_id=app_request.request_id, session=session)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"the flow doesn't support ({app_request.country}, {app_request.account_type}) yet"
        ) from error

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()

        logging.error("error while committing session"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"cannot create application - {error.orig} - sql: {error.statement}",
        ) from error

    return app_response

@router.post("/submit_step/{step_name}", response_model=SubmitStepResponse, status_code=status.HTTP_200_OK)
def post_step(step_name: str, form_payload: dict, resume_token: str = Header(alias="Resume-Token"),
              session: Session = Depends(get_onboarding_db)):
    """
    endpoint that submits a given step

    Args:
        step_name (str): the step id
        form_payload (dict): the actual data of the form
        resume_token (str): the resume token
        session (Session, optional): db session. Defaults to Depends(get_onboarding_db).
    """
    try:
        step_response: SubmitStepResponse = submit_step(step_name=step_name, form_payload=form_payload,
                                    token=resume_token, session=session)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no application with this token exists"
        ) from error

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()

        logging.error("error while committing session")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"cannot submit step - {error.orig}") from error

    return step_response


@router.get("/progress_status", response_model=ProgressResponse)
def get_progress(resume_token: str = Header(alias="Resume-Token"), session: Session = Depends(get_onboarding_db)):
    """
    endpoint for getting the status of an app

    Args:
        resume_token (str): the resume token
        session (Session, optional): the db session. Defaults to Depends(get_onboarding_db).
    """
    try:

        progress = read_progress(token=resume_token, session=session)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no application with this token exists"
        ) from error

    return progress


@router.post("/abandon", status_code=status.HTTP_200_OK)
def abandon(resume_token: str = Header(alias="Resume-Token"), session: Session = Depends(get_onboarding_db)):
    """
    endpoint for abandoning an application

    Args:
        resume_token (str, optional): the resume token. Defaults to Header(alias="Resume-Token").
        session (Session, optional): the db session. Defaults to Depends(get_onboarding_db).
    """
    try:
        _ = abandon_application(token=resume_token, session=session)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no application with this token exists"
        ) from error

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        logging.error("error while committing abandoned application")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"can't abandon application - {error.orig}") from error

    return JSONResponse(status_code=status.HTTP_200_OK, content="application is now abandoned")


@router.get('/decision', response_model=DecisionRecord, status_code=status.HTTP_200_OK)
def get_decision(resume_token: str = Header(alias="Resume-Token"), session: Session = Depends(get_onboarding_db)):
    """
    endpoint for returning the decision of a given app

    Args:
        resume_token (str, optional): the resume token. Defaults to Header(alias="Resume-Token").
        session (Session, optional): the db session. Defaults to Depends(get_onboarding_db).
    """
    try:
        decision: DecisionRecord = read_decision(token=resume_token, session=session)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no application with this token exists"
        ) from error

    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no decision found for this app")

    return decision


@router.get("/audit", response_model=AuditTrail, status_code=status.HTTP_200_OK)
def get_audit(resume_token: str = Header(alias="Resume-Token"), session: Session = Depends(get_onboarding_db)):
    """
    endpoint that returns the audit trail of a given app

    Args:
        resume_token (str, optional): the resume token. Defaults to Header(alias="Resume-Token").
        session (Session, optional): the db session. Defaults to Depends(get_onboarding_db).
    """
    try:
        audit_trail: AuditTrail = read_audit(token=resume_token, session=session)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no application with this token exists"
        ) from error

    return audit_trail
