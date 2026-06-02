"""
Module for base pydantic models for businesses
"""

from pydantic import BaseModel

class BaseCompanyDetailsForm(BaseModel):
    """
    Form for company details
    """
    company_name: str
    registration_number: str

