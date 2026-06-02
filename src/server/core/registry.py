"""
Builds lists of steps for private and business flows, based on (country, forms)
"""

from typing import Callable
from pydantic import BaseModel

from server.core.gates import block_on_error, terminate_on_rejection
from server.core.steps import StepDefinition
from server.models.common import AccountType, Country

from server.models.sweden_private import FORMS as SWEDEN_PRIVATE_FORMS
from server.models.sweden_business import FORMS as SWEDEN_BUSINESS_FORMS
from server.models.country_private_stub import FORMS as COUNTRY_PRIVATE_FORMS_STUB
from server.models.country_business_stub import FORMS as COUNTRY_BUSINESS_FORMS_STUB

from server.models.sweden_private import MAPPERS as SWEDEN_PRIVATE_MAPPERS
from server.models.sweden_business import MAPPERS as SWEDEN_BUSINESS_MAPPERS
from server.models.country_private_stub import MAPPERS as COUNTRY_PRIVATE_MAPPERS_STUB
from server.models.country_business_stub import MAPPERS as COUNTRY_BUSINESS_MAPPERS_STUB


def _private_steps(forms: dict[str, type[BaseModel]]) -> list[StepDefinition]:
    """
    Creates the steps for a private account flow

    Args:
        forms (dict): Mapping of step to Pydantic form model
        for example  {"personal_details": PersonalDetailsForm}

    Returns:
        (list): list of StepDefinition for the private flow.
    """
    return [
        StepDefinition(
            name="personal_details",
            form_schema=forms.get("personal_details"),
            integrations=["identity", "sanctions"],
            gate=terminate_on_rejection
        ),
        StepDefinition(
            name="contact_info",
            form_schema=forms.get("contact_info")
        ),
        StepDefinition(
            name="employment",
            form_schema=forms.get("employment"),
            integrations=["credit"],
            gate=block_on_error
        ),
        StepDefinition(
            name="bank_account",
            form_schema=forms.get("bank_account"),
            integrations=["bank_account"],
            gate=block_on_error
        ),
        StepDefinition(
            name="consent",
            form_schema=forms.get("consent")
        ),
    ]


def _business_steps(forms: dict[str, type[BaseModel]]) -> list[StepDefinition]:
    """
    Creates the steps for a business account flow

    Args:
        forms: Mapping of step to Pydantic model
        for example {"company_details": CompanyDetailsForm}

    Returns:
        List of StepDefinition for the business flow.
    """
    return [
        StepDefinition(
            name="company_details",
            form_schema=forms.get("company_details"),
            integrations=["registry", "sanctions"],
            gate=terminate_on_rejection,
        ),
        StepDefinition(
            name="personal_details",
            form_schema=forms.get("personal_details"),
            integrations=["identity"],
            gate=terminate_on_rejection,
        ),
        StepDefinition(
            name="contact_info",
            form_schema=forms.get("contact_info"),
        ),
        StepDefinition(
            name="bank_account",
            form_schema=forms.get("bank_account"),
            integrations=["bank_account"],
            gate=block_on_error,
        ),
        StepDefinition(
            name="consent",
            form_schema=forms.get("consent")
        ),
    ]


FLOWS: dict[tuple[Country, AccountType], list[StepDefinition]] = {
    (Country.sweden, AccountType.private): _private_steps(
        forms=SWEDEN_PRIVATE_FORMS
    ),
    (Country.sweden, AccountType.business): _business_steps(
        forms=SWEDEN_BUSINESS_FORMS
    ),
    # Using stubs for the rest
    (Country.poland, AccountType.private): _private_steps(
        forms=COUNTRY_PRIVATE_FORMS_STUB
    ),
    (Country.poland, AccountType.business): _business_steps(
        forms=COUNTRY_BUSINESS_FORMS_STUB
    ),
    (Country.spain, AccountType.private): _private_steps(
        forms=COUNTRY_PRIVATE_FORMS_STUB
    ),
    (Country.spain, AccountType.business): _business_steps(
        forms=COUNTRY_BUSINESS_FORMS_STUB
    ),
}

MAPPERS: dict[tuple[Country, AccountType], dict[str, Callable[[dict], dict]]] = {
    (Country.sweden, AccountType.private): SWEDEN_PRIVATE_MAPPERS,
    (Country.sweden, AccountType.business): SWEDEN_BUSINESS_MAPPERS,
    (Country.poland, AccountType.private): COUNTRY_PRIVATE_MAPPERS_STUB,
    (Country.poland, AccountType.business): COUNTRY_BUSINESS_MAPPERS_STUB,
    (Country.spain, AccountType.private): COUNTRY_PRIVATE_MAPPERS_STUB,
    (Country.spain, AccountType.business): COUNTRY_BUSINESS_MAPPERS_STUB,
}