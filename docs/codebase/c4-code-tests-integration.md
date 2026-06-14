# C4 Code Level: Integration Tests

## Overview

- **Location**: `backend/tests/integration/`
- **Runner**: pytest
- **Current coverage**: 24 tests across three modules.
- **Purpose**: Validate API composition, dashboard contracts, CORS, and the DB-backed demo.

## `test_application_api.py`

Sixteen tests use FastAPI `TestClient` and a fake unit of work to cover:

- job creation and deterministic intake enrichment
- application creation, listing, missing jobs, and state transitions
- score persistence and score audit events
- policy persistence, stored-score context, review outcomes, and missing applications
- executor dry-run persistence, idempotent reuse, missing applications, and mandatory policy
- complete audit-summary responses and missing applications

The tests assert policy-before-execution and verify executor attempt/result audit events.

## `test_cors_and_dashboard.py`

Seven tests cover:

- CORS headers on health and audit responses
- manual intake job-description controls
- sample-job prefilling
- state progression controls
- workflow readiness guards
- human-readable audit timeline summaries

These tests read the static frontend artifacts and protect the dashboard-to-API contract.

## `test_seed_to_dashboard.py`

One PostgreSQL-backed test runs the demo seed and verifies the audit endpoint. It requires
the configured database environment and is the integration check for persisted M1 records.

## Dependencies

- FastAPI `TestClient`
- pytest
- application dependency overrides and fakes
- PostgreSQL for the seed-to-dashboard test
