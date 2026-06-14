# C4 Code Level: Unit Tests

## Overview

- **Location**: `backend/tests/unit/`
- **Runner**: pytest
- **Current coverage**: 40 tests across nine modules.
- **Purpose**: Validate deterministic domain behavior, constraints, and dry-run planning.

## Modules

| Module | Tests | Coverage |
|---|---:|---|
| `test_policy_engine.py` | 9 | Confidence, modes, red flags, recommendations, score, missing data |
| `test_state_machine.py` | 7 | Valid lifecycle and invalid/terminal transitions |
| `test_application_scoring.py` | 4 | Complete, sparse, red-flag, and classified job scoring |
| `test_job_intake_classification.py` | 4 | Classification, preservation, sparse input, salary false positives |
| `test_model_constraints.py` | 7 | Cascades, state defaults, audit preservation, idempotency, executor metadata, replay indexes, value-check metadata |
| `test_demo_seed.py` | 1 | Seeded policy and dry-run audit workflow |
| `test_executor_stub.py` | 1 | Side-effect-free plan details and safeguards |
| `test_tracker_executor_contract.py` | 3 | Executor request/result metadata matching |
| `test_tracker_submission_workflow.py` | 4 | Guarded submission workflow and direct-state bypass protection |

## Architecture-Critical Assertions

The suite checks:

- invalid workflow transitions are rejected
- event log rows do not cascade-delete with applications
- policy decision and executor action rows do not cascade-delete with applications
- generated application-owned placeholder records do cascade
- executor idempotency keys are unique
- executor request metadata is persisted and indexed
- stable M1 value-check constraints are declared on ORM models
- tracker rejects executor results with mismatched request metadata
- event-log replay indexes exist
- policy decisions expose deterministic outcomes and overrides
- dry-run executor plans declare no side effects
- generic state updates cannot bypass guarded submission prerequisites

Database model constraint tests use SQLite metadata where possible. PostgreSQL migration
behavior remains covered by CI migration execution and the integration environment.
