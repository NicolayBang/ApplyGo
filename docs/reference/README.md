# Reference Artifacts

This folder holds generated reference snapshots that may help with review, debugging, or
comparison work.

These artifacts are not the authoritative schema source of truth.

For ApplyPilot, the authoritative database definition remains:

- Alembic migrations in `backend/alembic/versions/`
- `docs/contracts/database-schema-contract.md`
- implemented ORM/models and validated migration flow

Current artifact:

- `postgres-schema-reference-2026-06-16.sql` - schema-only `pg_dump` snapshot generated from the
  local Docker PostgreSQL instance on 2026-06-16.
