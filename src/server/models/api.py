"""
request and response models for api
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from server.models.common import AccountType, Country, StepStatus

class CreateAppRequest(BaseModel):
    """
    model for the create_app request
    """
    country: Country
    account_type: AccountType
    request_id: UUID

class CreateAppResponse(BaseModel):
    """
    model for the create_app response
    """
    app_id: UUID
    resume_token: str
    current_step: str

class SubmitStepResponse(BaseModel):
    """
    model for the submit_step response
    """
    step_status: StepStatus
    current_step: str | None

class ProgressResponse(BaseModel):
    """
    model for the progress report
    """
    total_steps: int = 0
    completed_steps: list[str] = [] # this is handled correctly by pydantic, as it creates a deepcopy
    current_step: str | None = None
    remaining_steps: list[str] = [] # same here

class StepRecord(BaseModel):
    """
    pydantic model for the steps, to decouple the api
    layer from ORMs
    """
    model_config = ConfigDict(from_attributes=True)

    step_id: str = Field(validation_alias="step_name")
    status: str
    form_data: dict
    created_at: datetime

class IntegrationRecord(BaseModel):
    """
    pydantic model for the integrations, to decouple the api
    layer from ORMs
    """
    model_config = ConfigDict(from_attributes=True)

    integration_name: str
    status: str
    response_payload: dict | None
    created_at: datetime

class DecisionRecord(BaseModel):
    """
    pydantic model for the decision, to decouple the api
    layer from ORMs
    """
    model_config = ConfigDict(from_attributes=True)

    outcome: str
    reasons: list
    decided_at: datetime

class AuditTrail(BaseModel):
    """
    model for the audit trail
    """
    steps: list[StepRecord]
    integrations: list[IntegrationRecord]
    decision: DecisionRecord | None
