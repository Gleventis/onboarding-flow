"""CLI flow runner"""

import argparse
import json
import sys
import uuid

from httpx import Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.fixtures import BUSINESS_FIXTURES, PRIVATE_FIXTURES

console = Console()


def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser for the CLI flow runner.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="cli.run_flow",
        description="Run an onboarding flow scenario against the API.",
    )
    parser.add_argument(
        "--country",
        required=True,
        choices=["sweden"],
        help="Country for the onboarding flow (e.g. sweden).",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["private", "business"],
        dest="account_type",
        help="Account type: private or business.",
    )
    parser.add_argument(
        "--scenario",
        required=True,
        choices=["happy", "rejected", "manual-review"],
        help="Scenario to run (e.g. happy, rejected, manual-review).",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        default=False,
        help="Skip interactive pauses between steps.",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the onboarding API (default: http://localhost:8000).",
    )
    return parser


def create_application(
    client: Client, country: str, account_type: str
) -> tuple[str, str]:
    """
    Create a new onboarding application via the API

    Args:
        client: httpx Client instance configured with base_url (e.g. Client(base_url="http://localhost:8000")).
        country: Country code for the flow
        account_type: Account type

    Returns:
        Tuple of (resume_token, current_step).
    """
    response = client.post(
        url="/application/create",
        json={
            "country": country,
            "account_type": account_type,
            "request_id": str(uuid.uuid4()),
        },
    )
    response.raise_for_status()
    data = response.json()
    return data.get("resume_token"), data.get("current_step")


def submit_step(
    client: Client, step_name: str, payload: dict, token: str
) -> tuple[str, str | None]:
    """
    Submit a step's form data to the API.

    Args:
        client: httpx Client instance .
        step_name: The step identifier
        payload: Form data dict matching the step schema
        token: Resume token from create_application

    Returns:
        Tuple of (step_status, current_step). current_step is None when flow ends.
    """
    response = client.post(
        url=f"/application/submit_step/{step_name}",
        json=payload,
        headers={"Resume-Token": token},
    )
    response.raise_for_status()
    data = response.json()
    return data.get("step_status"), data.get("current_step")


def get_decision(client: Client, token: str) -> dict:
    """
    Fetch the final decision for an application

    Args:
        client: httpx Client instance
        token: Resume token

    Returns:
        Decision dict with outcome, reasons, and decided_at.
    """
    response = client.get(
        url="/application/decision",
        headers={"Resume-Token": token},
    )
    response.raise_for_status()
    return response.json()


def get_audit(client: Client, token: str) -> dict:
    """
    Fetch the audit trail for an application

    Args:
        client: httpx Client instance
        token: Resume token

    Returns:
        Audit trail dict with steps, integrations, and decision.
    """
    response = client.get(
        url="/application/audit",
        headers={"Resume-Token": token},
    )
    response.raise_for_status()
    return response.json()


def load_fixtures(account_type: str, scenario: str) -> dict[str, dict]:
    """
    Load fixture data for the given account type and scenario

    Args:
        account_type: Account type
        scenario: Scenario name

    Returns:
        Dict mapping step names to their form payloads.
    """
    fixtures = PRIVATE_FIXTURES if account_type == "private" else BUSINESS_FIXTURES
    scenario_data = fixtures.get(scenario)
    if scenario_data is None:
        sys.exit(f"error: no fixtures for scenario '{scenario}' in '{account_type}'")
    return scenario_data


def run_flow(
    base_url: str,
    country: str,
    account_type: str,
    scenario: str,
    auto: bool,
) -> None:
    """
    Execute the full onboarding flow against the API.

    Args:
        base_url: API base URL
        country: Country code
        account_type: Account type
        scenario: Scenario name
        auto: If True, skip interactive pauses
    """
    fixtures = load_fixtures(account_type=account_type, scenario=scenario)

    console.print(Panel(
        f"[bold]{country}[/] / [bold]{account_type}[/] / [bold]{scenario}[/]\n"
        f"API: {base_url}",
        title="Onboarding Flow",
    ))

    with Client(base_url=base_url, verify=False) as client:
        token, current_step = create_application(
            client=client, country=country, account_type=account_type
        )
        console.print(f"\n[green]✓[/] Application created  token=[dim]{token}[/]  step=[cyan]{current_step}[/]\n")

        while current_step:
            payload = fixtures.get(current_step)
            if payload is None:
                console.print(f"[yellow]⚠[/] No fixture data for step [bold]{current_step}[/], stopping.")
                break

            console.print(f"[cyan]→[/] Submitting [bold]{current_step}[/]")
            console.print(f"  {json.dumps(payload, indent=2)}", highlight=False)

            if not auto:
                input("  press Enter to submit...")

            step_status, next_step = submit_step(
                client=client,
                step_name=current_step,
                payload=payload,
                token=token,
            )

            status_color = {"completed": "green", "blocked": "yellow", "terminated": "red"}.get(step_status, "white")
            console.print(f"  [{status_color}]{step_status}[/] → next: [cyan]{next_step or 'done'}[/]\n")

            if step_status in ("blocked", "terminated"):
                break

            current_step = next_step

        # decision
        try:
            decision = get_decision(client=client, token=token)
            outcome = decision.get("outcome", "unknown")
            outcome_color = {"approved": "green", "rejected": "red", "manual_review": "yellow"}.get(outcome, "white")
            reasons = decision.get("reasons", [])

            console.print(Panel(
                f"[{outcome_color} bold]{outcome.upper()}[/]"
                + (f"\nReasons: {', '.join(reasons)}" if reasons else ""),
                title="Decision",
            ))
        except Exception:
            console.print("[dim]No decision available.[/]")

        # audit
        try:
            audit = get_audit(client=client, token=token)
            steps = audit.get("steps", [])
            if steps:
                table = Table(title="Audit Trail")
                table.add_column("Step", style="cyan")
                table.add_column("Status")
                table.add_column("Created At", style="dim")

                for s in steps:
                    status = s.get("status", "")
                    color = {"completed": "green", "blocked": "yellow", "terminated": "red"}.get(status, "white")
                    table.add_row(
                        s.get("step_id", ""),
                        f"[{color}]{status}[/]",
                        s.get("created_at", ""),
                    )
                console.print(table)
        except Exception:
            console.print("[dim]Audit trail unavailable.[/]")


def main() -> None:
    """
    Parse arguments and run the onboarding flow scenario
    """
    parser = build_parser()
    args = parser.parse_args()
    run_flow(
        base_url=args.base_url,
        country=args.country,
        account_type=args.account_type,
        scenario=args.scenario,
        auto=args.auto,
    )


if __name__ == "__main__":
    main()
