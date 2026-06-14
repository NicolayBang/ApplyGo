# C4 Code Level: Unit Tests

## Overview

- **Location**: `backend/tests/unit/`
- **Runner**: pytest
- **Current coverage**: 30 tests across seven modules.
- **Purpose**: Validate deterministic domain behavior, constraints, and dry-run planning.

## Modules

| Module | Tests | Coverage |
|---|---:|---|
| `test_policy_engine.py` | 9 | Confidence, modes, red flags, recommendations, score, missing data |
| `test_state_machine.py` | 7 | Valid lifecycle and invalid/terminal transitions |
| `test_application_scoring.py` | 4 | Complete, sparse, red-flag, and classified job scoring |
| `test_job_intake_classification.py` | 4 | Classification, preservation, sparse input, salary false positives |
| `test_model_constraints.py` | 4 | Cascades, audit preservation, idempotency, replay indexes |
| `test_demo_seed.py` | 1 | Seeded policy and dry-run audit workflow |
| `test_executor_stub.py` | 1 | Side-effect-free plan details and safeguards |

## Architecture-Critical Assertions

The suite checks:

- invalid workflow transitions are rejected
- event log rows do not cascade-delete with applications
- application-owned operational records do cascade
- executor idempotency keys are unique
- event-log replay indexes exist
- policy decisions expose deterministic outcomes and overrides
- dry-run executor plans declare no side effects

Database model constraint tests use SQLite metadata where possible. PostgreSQL migration
behavior remains covered by CI migration execution and the integration environment.
