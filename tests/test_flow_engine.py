"""
contains test cases for the flow of the onboarding
"""
import pytest

from server.core.registry import FLOWS, MAPPERS

from server.core.steps import StepDefinition, get_step, next_step
from server.models.common import Country, AccountType, IntegrationResult, IntegrationStatus, StepStatus

@pytest.fixture
def sweden_private_flow() -> list[StepDefinition]:
    return FLOWS.get((Country.sweden, AccountType.private))


@pytest.fixture
def sweden_business_flow() -> list[StepDefinition]:
    return FLOWS.get((Country.sweden, AccountType.business))


@pytest.fixture
def sweden_private_mappers() -> dict:
    return MAPPERS.get((Country.sweden, AccountType.private))


@pytest.fixture
def sweden_business_mappers() -> dict:
    return MAPPERS.get((Country.sweden, AccountType.business))


@pytest.fixture
def success_result():
    return IntegrationResult(status=IntegrationStatus.success, outcome="verified")


@pytest.fixture
def timeout_result():
    return IntegrationResult(status=IntegrationStatus.timeout, outcome=None)


@pytest.fixture
def confirmed_hit_result():
    return IntegrationResult(status=IntegrationStatus.success, outcome="confirmed_hit")


def test_sweden_private_step_order(sweden_private_flow):
    """
    test case for the step order in the private sweden account
    """

    step_names = [step.name for step in sweden_private_flow]

    expected_step_order = ["personal_details", "contact_info", "employment", "bank_account", "consent"]

    assert step_names == expected_step_order, "wrong order of steps"


def test_sweden_business_step_order(sweden_business_flow):
    """
    test case for the step order in the business sweden account
    """
    step_names = [step.name for step in sweden_business_flow]

    expected_step_order = ["company_details", "personal_details", "contact_info", "bank_account", "consent"]

    assert step_names == expected_step_order


def test_none_after_last_step(sweden_private_flow):
    """
    test case that returns none after last step
    """
    assert next_step(steps=sweden_private_flow, current="consent") is None, "next_step should return None"


def test_all_flows_registered():
    """
    tests that flow is generated properly
    """
    assert len(FLOWS) == 6, "missing flow"
    for flow in FLOWS.values():
        assert len(flow) == 5, "missing step"



def test_terminate_gate_completes_on_clean_results(sweden_private_flow, success_result):
    """
    test case that terminate_on_rejection gate completes when results are clean
    """
    step = get_step(steps=sweden_private_flow, name="personal_details")

    result = step.gate([success_result, success_result])

    assert result == StepStatus.completed


def test_terminate_gate_terminates_on_rejection(sweden_private_flow, confirmed_hit_result):
    """
    test case that terminate_on_rejection gate terminates on rejection outcome
    """
    step = get_step(steps=sweden_private_flow, name="personal_details")

    result = step.gate([confirmed_hit_result])

    assert result == StepStatus.terminated


def test_terminate_gate_blocks_on_timeout(sweden_private_flow, timeout_result):
    """
    test case that terminate_on_rejection gate blocks on timeout
    """
    step = get_step(steps=sweden_private_flow, name="personal_details")

    result = step.gate([timeout_result])

    assert result == StepStatus.blocked


def test_block_on_error_blocks_on_failure(sweden_private_flow):
    """
    test case that block_on_error gate blocks on failure status
    """
    step = get_step(steps=sweden_private_flow, name="employment")

    failure_result = IntegrationResult(status=IntegrationStatus.failure, outcome=None)

    result = step.gate([failure_result])

    assert result == StepStatus.blocked


def test_block_on_error_completes_on_success(sweden_private_flow, success_result):
    """
    test case that block_on_error gate completes on success
    """
    step = get_step(steps=sweden_private_flow, name="employment")

    result = step.gate([success_result])

    assert result == StepStatus.completed


def test_block_on_error_blocks_on_timeout(sweden_private_flow, timeout_result):
    """
    test case that block_on_error gate blocks on timeout
    """
    step = get_step(steps=sweden_private_flow, name="bank_account")

    result = step.gate([timeout_result])

    assert result == StepStatus.blocked


def test_pass_through_always_completes(sweden_private_flow, timeout_result):
    """
    test case that pass_through gate always completes regardless of results
    """
    step = get_step(steps=sweden_private_flow, name="contact_info")

    result = step.gate([timeout_result])

    assert result == StepStatus.completed


def test_se_private_identity_mapper(sweden_private_mappers):
    """
    test case for the sweden private identity mapper
    """
    form_data = {"personnummer": "199001011234", "first_name": "Anna", "last_name": "Svensson"}

    payload = sweden_private_mappers.get("identity")(form_data)

    assert payload == {"personal_id": "199001011234"}


def test_se_private_sanctions_mapper(sweden_private_mappers):
    """
    test case for the sweden private sanctions mapper
    """
    form_data = {"first_name": "Anna", "last_name": "Svensson"}

    payload = sweden_private_mappers.get("sanctions")(form_data)

    assert payload == {"name": "Anna Svensson"}


def test_se_private_credit_mapper(sweden_private_mappers):
    """
    test case for the sweden private credit mapper
    """
    form_data = {"income": 45000.0, "debt": 3000.0, "employer_name": "X", "employment_status": "employed"}

    payload = sweden_private_mappers.get("credit")(form_data)

    assert payload == {"income": 45000.0, "debt": 3000.0}


def test_se_private_bank_account_mapper(sweden_private_mappers):
    """
    test case for the sweden private bank_account mapper
    """
    form_data = {"iban": "SE123", "bank_name": "Nordea", "account_holder_name": "Anna Svensson"}

    payload = sweden_private_mappers.get("bank_account")(form_data)

    assert payload == {"iban": "SE123", "account_name": "Anna Svensson"}


def test_se_business_sanctions_mapper(sweden_business_mappers):
    """
    test case for the sweden business sanctions mapper
    """
    form_data = {"company_name": "Acme AB", "registration_number": "5566778899"}

    payload = sweden_business_mappers.get("sanctions")(form_data)

    assert payload == {"name": "Acme AB"}


def test_se_business_registry_mapper(sweden_business_mappers):
    """
    test case for the sweden business registry mapper
    """
    form_data = {"registration_number": "5566778899", "company_name": "Acme AB"}

    payload = sweden_business_mappers.get("registry")(form_data)

    assert payload == {"registration_number": "5566778899", "country": "sweden"}


def test_se_business_identity_mapper(sweden_business_mappers):
    """
    test case for the sweden business identity mapper
    """
    form_data = {"personnummer": "198505051234", "first_name": "Erik", "last_name": "Johansson"}

    payload = sweden_business_mappers.get("identity")(form_data)

    assert payload == {"personal_id": "198505051234"}
