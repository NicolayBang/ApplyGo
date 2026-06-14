# C4 Code Level: Integration Tests

## Overview

- **Location**: `backend/tests/integration/`
- **Runner**: pytest
- **Current coverage**: 29 tests across three modules.
- **Purpose**: Validate API composition, dashboard contracts, CORS, and the DB-backed demo.

## `test_application_api.py`

Nineteen tests use FastAPI `TestClient` and a fake unit of work to cover:

- job creation and deterministic intake enrichment
- application creation, listing, missing jobs, and state transitions
- score persistence and score audit events
- policy persistence, stored-score context, review outcomes, and missing applications
- executor dry-run metadata, persistence, idempotent reuse, missing applications, and mandatory policy
- guarded `Submitted` transitions requiring allowed policy and executor evidence
- complete audit-summary responses and missing applications

The tests assert policy-before-execution and verify executor request metadata plus
attempt/result audit events.

## `test_cors_and_dashboard.py`

Eight tests cover:

- CORS headers on health and audit responses
- manual intake job-description controls
- sample-job prefilling
- state progression controls
- workflow readiness guards
- human-readable audit timeline summaries

These tests read the static frontend artifacts and protect the dashboard-to-API contract.

## `test_seed_to_dashboard.py`

Two PostgreSQL-backed tests run against the configured database environment:

- demo seed to audit endpoint validation for persisted M1 records
- direct invalid-write checks proving M1 value constraints reject bad database values

## Dependencies

- FastAPI `TestClient`
- pytest
- application dependency overrides and fakes
- PostgreSQL for the seed-to-dashboard and value-constraint tests
