"""Make documents.application_id nullable (M5 compatibility window).

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-20

PR2.5 compatibility fix for Issue #219. Migration ``0012`` transformed ``documents``
into the reusable M5 logical document library but retained the legacy single-owner
``application_id`` column as ``NOT NULL``. A reusable logical document has no single
application owner (see ``docs/contracts/m5-packet-document-answer-contract.md``), so a
newly created library document cannot supply ``application_id``.

This migration relaxes ``documents.application_id`` to ``NULL``-able so new logical
documents may omit it, while the legacy column, its foreign key, index, and
``ON DELETE CASCADE`` behavior are preserved for existing rows during the M5
compatibility window. A later PR removes the legacy column entirely after readers
switch off it.

The change is metadata-only: no row is inserted, deleted, or rewritten, and the M5
backfill from ``0012`` is untouched. ``downgrade`` restores ``NOT NULL`` (which requires
that no ``NULL`` ``application_id`` rows exist at downgrade time).
"""

from __future__ import annotations

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Metadata-only: drop NOT NULL while keeping the column, FK, index, and cascade.
    op.alter_column(
        "documents",
        "application_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    # Restore NOT NULL. Requires that no NULL application_id rows exist.
    op.alter_column(
        "documents",
        "application_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
