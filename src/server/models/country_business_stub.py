"""
forms for a country business
"""

from typing import Callable
from pydantic import BaseModel
from server.models.base_businesses import BaseCompanyDetailsForm
from server.models.base_individuals import (BaseBankAccountForm, BaseConsentForm, BaseContactInfoForm,
                                            BasePersonalForm)

FORMS: dict[str, type[BaseModel]] = {
    "company_details": BaseCompanyDetailsForm,
    "personal_details": BasePersonalForm,
    "contact_info": BaseContactInfoForm,
    "bank_account": BaseBankAccountForm,
    "consent": BaseConsentForm
}

MAPPERS: dict[str, Callable[[dict], dict]] = {
    "identity": lambda data: {"personal_id": data.get("personal_id", "stub")}, # no real value to map to
    "sanctions": lambda data: {"name": data.get("company_name")},
    "registry": lambda data: {"registration_number": data.get("registration_number"), "country": "stub"},
    "bank_account": lambda data: {"iban": data.get("iban"), "account_name": data.get("account_holder_name")},
}
