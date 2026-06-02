"""
Module that holds the base pydantic models for individuals
"""

from pydantic import BaseModel

class BasePersonalForm(BaseModel):
    """
    Form for personal identification
    """
    first_name: str
    last_name: str

class BaseContactInfoForm(BaseModel):
    """
    Form for contact info
    """
    street: str
    city: str
    postal_code: str
    phone: str
    email: str

class BaseEmploymentForm(BaseModel):
    """
    Form for Employment info
    """
    employer_name: str
    employment_status: str
    income: float
    debt: float

class BaseBankAccountForm(BaseModel):
    """
    Form for bank account verification
    """
    iban: str
    bank_name: str
    account_holder_name: str

class BaseConsentForm(BaseModel):
    """
    Form for consent
    """
    terms_accepted: bool

