"""
module that holds the rules for set the status for the application - chain of responsibility
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from server.models.common import DecisionOutcome, IntegrationResult

class RuleHandler(ABC):
    """
    Abstract class for the rule handler
    """

    def __init__(self):
        self.next: RuleHandler = None

    def set_next(self, handler: RuleHandler) -> RuleHandler:
        """
        sets the handler for the next rule

        Args:
            handler (RuleHandler): a rule handler

        Returns:
            RuleHandler: the next rule handler
        """
        self.next = handler
        return handler

    def handle(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, list[str]]:
        """
        handles a list of integration results and returns a decision

        Args:
            results (list[IntegrationResult]): a list of integrations

        Returns:
            tuple[DecisionOutcome, list[str]]: (the outcome based on the rules, list of reasons)
        """
        decision = self.evaluate(results)

        if decision is not None:
            outcome, reason = decision
            return (outcome, [reason])

        if self.next:
            return self.next.handle(results=results)

        return (DecisionOutcome.approved, [])

    @abstractmethod
    def evaluate(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, str]  | None:
        """
        evaluates if the rule matches

        Args:
            results (list[IntegrationResult]): the list of integrations

        Returns:
           tuple[DecisionOutcome, str] | None: the outcome of the decision and the name of the reason or None
        """

class SanctionsConfirmedHit(RuleHandler):
    """
    class handling the case where a sanction returned confirmed_hit
    """

    def evaluate(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, str] | None:
        """
        evaluates the confirmed_hit rule

        Args:
            results (list[IntegrationResult]): list of integrations

        Returns:
            tuple[DecisionOutcome, str] | None: the outcome if confirmed hit with the reason, None otherwise
        """
        for result in results:
            if result.outcome == "confirmed_hit":
                return (DecisionOutcome.rejected, "sanction_confirmed_hit")
        return None

class SanctionsPossibleHit(RuleHandler):
    """
    class handling the case where a sanction returned possible_hit
    """

    def evaluate(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, str] | None:
        """
        evaluates the possible_hit rule

        Args:
            results (list[IntegrationResult]): list of integrations

        Returns:
            tuple[DecisionOutcome, str] | None: the outcome if possible hit with the reason, None otherwise
        """
        for result in results:
            if result.outcome == "possible_hit":
                return (DecisionOutcome.manual_review, "sanction_possible_hit")
        return None

class IdentityRejected(RuleHandler):
    """
    class handling the case where the identity integration returned expired_id or document_mismatch
    """

    def evaluate(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, str] | None:
        """
        evaluates the identity rule

        Args:
            results (list[IntegrationResult]): list of integrations

        Returns:
            tuple[DecisionOutcome, str] | None: the outcome if expired_id with the reason or document_mismatch,
            None otherwise
        """
        for result in results:
            if result.outcome == "expired_id" or result.outcome == "document_mismatch":
                return (DecisionOutcome.rejected, "identity_rejected")
        return None

class IdentityManualReview(RuleHandler):
    """
    class handling the case where the identity integration requires manual review
    """
    def evaluate(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, str] | None:
        """
        evaluates the case where the identityt integration requires manual review

        Args:
            results (list[IntegrationResult]): list of integrations

        Returns:
           tuple[DecisionOutcome, str] | None: the outcome if requires manual review with the reason, None otherwise
        """
        for result in results:
            if result.outcome == "identity_manual_review":
                return (DecisionOutcome.manual_review, "identity_manual_review")
        return None

class Registry(RuleHandler):
    """
    class handling the case  where the registry integration returned dissolved, unknown_representative or missing_ubo
    """

    def evaluate(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, str] | None:
        """
        evaluates the registry rule

        Args:
            results (list[IntegrationResult]): list of integrations

        Returns:
            tuple[DecisionOutcome, str] | None: the outcome if dissolved, unknown_representative or missing_ubo, with the reason None otherwise
        """
        for result in results:
            if (
                result.outcome == "dissolved" or
                result.outcome == "unknown_representative" or
                result.outcome == "missing_ubo"
                ):
                return (DecisionOutcome.rejected, "registry_rejected")

        return None

class ScoreBelowThreshold(RuleHandler):
    """
    class handling the case where the score is below threshold
    """

    def evaluate(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, str] | None:
        """
        evaluates the below_threshold rule

        Args:
            results (list[IntegrationResult]): list of integrations

        Returns:
            tuple[DecisionOutcome, str] | None: the outcome if below_threshold with the reason, None otherwise
        """
        for result in results:
            if result.outcome == "below_threshold":
                return (DecisionOutcome.manual_review, "score_below_threshold")
        return None

class Income(RuleHandler):
    """
    class handling the case where income < 40000sek/month
    """

    def evaluate(self, results: list[IntegrationResult]) -> tuple[DecisionOutcome, str] | None:
        """
        evaluates the income rule

        Args:
            results (list[IntegrationResult]): list of integrations

        Returns:
            tuple[DecisionOutcome, str] | None: the outcome if below_income with reason, None otherwise
        """
        for result in results:
            if result.details and result.details.get("disposable_income", 0) < 40000:
                return (DecisionOutcome.manual_review, "low_disposable_income")
        return None


def build_cor() -> RuleHandler:
    """
    builds the chain of responsibility
    """
    chain = SanctionsConfirmedHit()

    chain.set_next(SanctionsPossibleHit())\
        .set_next(IdentityRejected())\
        .set_next(IdentityManualReview())\
        .set_next(Registry())\
        .set_next(ScoreBelowThreshold())\
        .set_next(Income())

    return chain
