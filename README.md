# Onboarding Flow

Onboarding app for Ikano clients. The users can select country and account type, and the app will map the input to the required steps and rules.

External integrations are mocked, with deterministic results.

A CLI is also provided to assist in testing.

Stack: Python 3.12, FastAPI, Pydantic, SQLAlchemy (sync), PostgreSQL

## Architecture

```
Routes(entry-point) -> Services(Orchestrator, integrations) -> Core (steps, registry, gates, rules) -> CRUD -> DB
```

### Design Patterns
1. Registry: Maps (country, account_type) to step definitions and payload transformers. Allows for flexibility when adding new countries, or new steps. To add a new country we just need to create a new module that exposes 'FORMS' and 'MAPPERS' and add it in the registry.
2. Strategy: The integration dispatch system. The orchestrator doesn't know anything about which integration to call at which point in time. It just passes a name and payload to the handler and the handler takes care of it. Adding new integrations is straight forward; write a new class with the same signature and register it in the dict.
3. Chain of Responsibility: Evaluation of integration reuslts/rules. Each rule has a concrete handler implementation. The integration result flows through this chain and if no handlers match it, then it falls through to the approved state.

## How It Works

### Building blocks

Each flow is built from:
- Steps — list of steps
- Forms — Pydantic models defining what data the user submits per step
- Mappers — transform form data into integration payloads (country-specific → generic)
- Integrations — external checks (identity, sanctions, credit, bank account, registry)

### Gates

Gates evaluate integration results and determine step outcome:

| Gate | Assigned to | Integrations | Triggers |
|------|-------------|--------------|----------|
| terminate_on_rejection | personal_details, company_details | identity, sanctions, registry | terminated if outcome in (failed, confirmed_hit, inactive); blocked if status is failure/timeout; completed otherwise |
| block_on_error | employment, bank_account | credit, bank_account | blocked if status is failure/timeout; completed otherwise |
| pass_through | contact_info, consent | none | always completed |

Step outcomes:
- **completed** → flow advances to next step
- **blocked** → flow paused (no retry mechanism in current implementation)
- **terminated** → application immediately rejected, flow ends

### Decision outcomes

After all steps complete, the Chain of Responsibility evaluates all integration results. Priority order:

| Rule | Outcome | Trigger |
|------|---------|---------|
| Sanctions confirmed hit | **rejected** | `confirmed_hit` |
| Sanctions possible hit | **manual_review** | `possible_hit` |
| Identity rejected | **rejected** | `expired_id`, `document_mismatch` |
| Identity manual review | **manual_review** | `identity_manual_review` |
| Registry invalid | **rejected** | `dissolved`, `unknown_representative`, `missing_ubo` |
| Score below threshold | **manual_review** | `below_threshold` |
| Low disposable income | **manual_review** | `disposable_income < 40000` |
| Default (no match) | **approved** | — |

First match wins — if multiple rules would match, only the highest-priority one fires.


## Database Schema

```
┌─────────────────────────────────┐
│          applications           │
├─────────────────────────────────┤
│ id              UUID PK         │
│ country         text            │
│ account_type    text            │
│ status          text            │
│ current_step_id text            │
│ request_id      UUID            │
│ resume_token    text            │
│ token_expiration_date timestamp │
│ created_at      timestamp       │
│ updated_at      timestamp       │
└──────────┬──────────────────────┘
           │ 1
           ├──────────────────┬────────────────────┐
           │ *                │ *                  │ 1
           ▼                  ▼                    ▼
┌────────────────────┐ ┌──────────────────────┐ ┌────────────────────┐
│      steps         │ │    integrations      │ │     decisions      │
├────────────────────┤ ├──────────────────────┤ ├────────────────────┤
│ id         int PK  │ │ id         int PK    │ │ id       int PK    │
│ application_id FK  │ │ application_id FK    │ │ application_id FK  │
│ step_name  text    │ │ step_name  text      │ │   (unique)         │
│ form_data  JSON    │ │ integration_name text│ │ outcome  text      │
│ status     text    │ │ request_payload JSON │ │ reasons  JSON      │
│ created_at ts      │ │ response_payload JSON│ │ decided_at ts      │
└────────────────────┘ │ status     text      │ └────────────────────┘
                       │ created_at ts        │
                       └──────────────────────┘
```

Audit trail: query all 3 child tables by `application_id`, ordered by `created_at`.

## Deterministic Mock Output

All integrations are deterministic mocks. Outcomes are controlled by specific field values — all other fields in CLI fixtures are cosmetic and can be changed freely.

| Integration | Trigger field | Pattern | Outcome |
|-------------|--------------|---------|---------|
| Identity | `personnummer` (last digit) | ends in `0` | `expired_id` → rejected |
| | | ends in `1` | `document_mismatch` → rejected |
| | | ends in `2` | `identity_manual_review` → manual_review |
| | | anything else | `verified` → pass |
| Sanctions | `first_name` (private) or `company_name` (business) | starts with `"confirmed"` | `confirmed_hit` → rejected |
| | | starts with `"possible"` | `possible_hit` → manual_review |
| | | anything else | `no_hit` → pass |
| Credit | `income - debt` (score) | score ≤ 49 | `below_threshold` → manual_review |
| | | score > 49 | `above_threshold` → pass |
| Bank account | `iban` | starts with `"name_mismatch"` | `name_mismatch` |
| | | starts with `"wrong_iban"` | `wrong_iban` |
| | | starts with `"unreachable"` | `unreachable` → timeout (blocked by gate) |
| | | anything else | `iban_verified` → pass |
| Registry | `registration_number` | starts with `"0"` | `dissolved` → rejected |
| | | starts with `"1"` | `unknown_representative` → rejected |
| | | starts with `"2"` | `missing_ubo` → rejected |
| | | anything else | `active_company` → pass |

### Example

``"personal_details": {
            "first_name": "confirmed_Anna",
            "last_name": "Target",
            "personnummer": "199001013",
        }``
will trigger the sanctions integration. Since the first name starts with confirmed it will return *confirmed_hit* and result in a *rejected* outcome.

## API Endpoints

All endpoints except `/create` require a `Resume-Token` header.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/application/create` | Start new application (country + account_type + request_id) |
| POST | `/application/submit_step/{step_name}` | Submit form data for a step |
| GET | `/application/progress_status` | Get current progress |
| POST | `/application/abandon` | Abandon an application |
| GET | `/application/decision` | Get final decision + reasons |
| GET | `/application/audit` | Get full audit trail |

## Assumptions

- No authentication/authorization
- No real external service calls — all integrations are deterministic mocks
- Single-instance, no concurrency handling
- All flows are linear (no branching/parallelism)
- All countries follow the same steps per account type (private template / business template)
- All countries follow the same decisioning rules (single CoR chain)
- No async
- Step submition is follows a linear path
- This is an API that only customers of Ikano will use. Employees will need a separate API to review and resolve manual_review applications

## Limitations

- Blocked steps have no retry/unblock path
- Integrations only see current step form data
- CoR is fail-open. If no rule matches then the result will flow through all the handlers and result in approved. Any unrecognized or new integration, without a corresponding rule will just flow through'
- CoR stops on first match, reviewers only have visibility of the first rule that failed.
- Abandoned is final, no way to resume
- A completed step can't be resubmitted
- All countries share the same rules and order of rules.
- All countries share the same step templates, different step orders, or new steps require new template functions

## Improvements

- **Payload mapping**: Currently uses a `MAPPERS` dict per country module. Ideal design: forms implement `to_{integration}_payload()` methods directly — no indirection, more discoverable, more testable.
- **Decisioning**: Evaluate all rules, collect all the results and return the worst outcome with corresponding reasons.
- **Fail-closed decisioning**: Create a final handler that approves a clean application, and make the default to be manual_review.
- **Blocked step recovery**: allow resubmission of the same step, wipe the previous attempt and run fresh
- **Country-specific decisioning**: Combine registry and CoR. Create a RULES registry dict, that maps (country, account_type) to a rule handler
- **Country-specific steps**: Modify the registry pattern for the steps. Each country_account_type module exposes a STEPS dict, remove the builder from the registry module and update the FLOWS dict.
- **Allow completed step resubmission**: Allow the user to submit new form to already existing step.
- **Non-Linear flow**: Allow submission of all steps in any order, or hybrid approach; group steps in ordered phases. Phases are ordered(phase 1 before phase 2) but steps within phases are not ordered.

## Next Steps

- Authentication (API key or token-based)
- Async integrations with real HTTP calls and circuit breaker
- Retry/resume mechanism for blocked steps
- Observability (structured logging, metrics, distributed tracing)

## How to Run

### Docker (recommended)

Spins up both the onboarding-flow app and the pg database

```bash
cd compose
docker compose up --build
```

App available at `http://localhost:8000`.


## Testing

```bash
uv sync --dev
pytest tests/ -q
```

36 tests covering:
- Flow engine — step progression, gate evaluation, payload mappers
- Decisioning — CoR chain priority, rule matching, edge cases

## CLI

Requires the onboarding app to be up and running.

After you have brought up the service run:

```bash

# Run a full flow scenario (requires the app to be running)
uv run onboarding-cli --country sweden --type private --scenario happy --auto
uv run onboarding-cli --country sweden --type business --scenario rejected --auto
```
