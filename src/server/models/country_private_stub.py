"""
forms for a country private
"""

from typing import Callable
from pydantic import BaseModel

from server.models.base_individuals import (BaseBankAccountForm, BaseConsentForm, BaseContactInfoForm,
                                            BaseEmploymentForm, BasePersonalForm)

FORMS: dict[str, type[BaseModel]] = {
    "personal_details": BasePersonalForm,
    "contact_info": BaseContactInfoForm,
    "employment": BaseEmploymentForm,
    "bank_account": BaseBankAccountForm,
    "consent": BaseConsentForm,
}

MAPPERS: dict[str, Callable[[dict], dict]] = {
    "identity": lambda data: {"personal_id": data.get("personal_id", "stub")}, # no real value to map to
    "sanctions": lambda data: {"name": f"{data.get('first_name')} {data.get('last_name')}"},
    "credit": lambda data: {"income": data.get("income"), "debt": data.get("debt")},
    "bank_account": lambda data: {"iban": data.get("iban"), "account_name": data.get("account_holder_name")},
}