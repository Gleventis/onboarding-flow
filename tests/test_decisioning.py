"""
contains test cases for the decisioning chain of responsibility
"""
import pytest

from server.core.rules import build_cor
from server.models.common import DecisionOutcome, IntegrationResult, IntegrationStatus


@pytest.fixture
def chain():
    return build_cor()


def test_all_clean_results_approved(chain):
    """
    test case that all clean results lead to approved
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="verified"),
        IntegrationResult(status=IntegrationStatus.success, outcome="no_hit"),
        IntegrationResult(status=IntegrationStatus.success, outcome="above_threshold"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.approved
    assert reasons == []


def test_empty_results_approved(chain):
    """
    test case that empty results lead to approved
    """
    outcome, reasons = chain.handle(results=[])

    assert outcome == DecisionOutcome.approved
    assert reasons == []


def test_sanctions_confirmed_hit_rejected(chain):
    """
    test case that confirmed_hit leads to rejected
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="confirmed_hit"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["sanction_confirmed_hit"]


def test_sanctions_possible_hit_manual_review(chain):
    """
    test case that possible_hit leads to manual_review
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="possible_hit"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.manual_review
    assert reasons == ["sanction_possible_hit"]


def test_identity_expired_id_rejected(chain):
    """
    test case that expired_id leads to rejected
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="expired_id"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["identity_rejected"]


def test_identity_document_mismatch_rejected(chain):
    """
    test case that document_mismatch leads to rejected
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="document_mismatch"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["identity_rejected"]


def test_identity_manual_review(chain):
    """
    test case that identity_manual_review leads to manual_review
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="identity_manual_review"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.manual_review
    assert reasons == ["identity_manual_review"]


def test_registry_dissolved_rejected(chain):
    """
    test case that dissolved leads to rejected
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="dissolved"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["registry_rejected"]


def test_registry_unknown_representative_rejected(chain):
    """
    test case that unknown_representative leads to rejected
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="unknown_representative"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["registry_rejected"]


def test_registry_missing_ubo_rejected(chain):
    """
    test case that missing_ubo leads to rejected
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="missing_ubo"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["registry_rejected"]


def test_score_below_threshold_manual_review(chain):
    """
    test case that below_threshold leads to manual_review
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="below_threshold"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.manual_review
    assert reasons == ["score_below_threshold"]


def test_low_disposable_income_manual_review(chain):
    """
    test case that disposable_income below 40000 leads to manual_review
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="above_threshold", details={"disposable_income": 30000}),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.manual_review
    assert reasons == ["low_disposable_income"]


def test_disposable_income_exactly_40000_approved(chain):
    """
    test case that disposable_income exactly 40000 is approved
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="above_threshold", details={"disposable_income": 40000}),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.approved
    assert reasons == []


def test_confirmed_hit_wins_over_expired_id(chain):
    """
    test case that confirmed_hit has higher priority than expired_id
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="confirmed_hit"),
        IntegrationResult(status=IntegrationStatus.success, outcome="expired_id"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["sanction_confirmed_hit"]


def test_possible_hit_wins_over_expired_id(chain):
    """
    test case that possible_hit has higher priority than identity rejection
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="possible_hit"),
        IntegrationResult(status=IntegrationStatus.success, outcome="expired_id"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.manual_review
    assert reasons == ["sanction_possible_hit"]


def test_confirmed_hit_wins_over_below_threshold(chain):
    """
    test case that confirmed_hit has higher priority than below_threshold
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="confirmed_hit"),
        IntegrationResult(status=IntegrationStatus.success, outcome="below_threshold"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["sanction_confirmed_hit"]


def test_identity_rejected_wins_over_below_threshold(chain):
    """
    test case that identity rejection has higher priority than score
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="expired_id"),
        IntegrationResult(status=IntegrationStatus.success, outcome="below_threshold"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.rejected
    assert reasons == ["identity_rejected"]


def test_unrecognized_outcome_approved(chain):
    """
    test case that unrecognized outcomes lead to approved
    """
    results = [
        IntegrationResult(status=IntegrationStatus.success, outcome="something_random"),
    ]

    outcome, reasons = chain.handle(results=results)

    assert outcome == DecisionOutcome.approved
    assert reasons == []
