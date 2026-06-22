"""Remove the legacy single-application compatibility fields from ``documents``.

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-21

Final M5 cutover for Issue #219. Migrations ``0012``/``0013`` transformed the M1
placeholder ``documents`` table into the reusable M5 logical document library while
retaining the legacy single-owner columns (``application_id`` cascade FK + index,
``content``, ``content_json``, ``version``) during a compatibility window. The M5
read-model API (PR3) reads exclusively from the logical library, immutable
``document_versions``, append-only ``application_documents``, and immutable
``application_answers`` tables, so the legacy columns now have no reader.

This migration removes the legacy compatibility surface:

- It first re-runs the M5 preservation invariant and aborts *before any DDL* if a
  legacy-owned ``documents`` row lacks its immutable ``document_versions`` payload or a
  matching ``application_documents`` attachment. The destructive DDL never runs against
  data that has not been fully represented in the M5 model, and PostgreSQL's
  transactional DDL guarantees no partial application even if a later statement fails.
- It then drops the legacy foreign key, ``ix_documents_application_id``, and the
  ``application_id``, ``content``, ``content_json``, and ``version`` columns.
- It retains ``id``, ``doc_type``, ``name``, ``is_archived``, ``created_at``, and
  ``updated_at`` on ``documents``, and leaves every M5 table, constraint, and
  ``ON DELETE RESTRICT`` retention behavior untouched.

``downgrade`` is intentionally **forward-only**. Once the M5 library is in real use, a
many-to-many document/version/attachment history cannot be losslessly reconstructed as
the retired single-owner model. The operational rollback path is a database snapshot
restore or a forward corrective migration, not an Alembic downgrade.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


# Legacy-owned ``documents`` rows that are not fully represented in the M5 model.
# A legacy-owned row (``application_id IS NOT NULL``) is preserved only when it has at
# least one immutable ``document_versions`` payload AND at least one
# ``application_documents`` attachment binding one of its versions to its owning
# application. Any returned row blocks the destructive cleanup.
_PRESERVATION_QUERY = sa.text(
    """
    SELECT d.id AS document_id, d.application_id AS application_id
    FROM documents d
    WHERE d.application_id IS NOT NULL
      AND (
        NOT EXISTS (
            SELECT 1 FROM document_versions dv
            WHERE dv.document_id = d.id
        )
        OR NOT EXISTS (
            SELECT 1
            FROM application_documents ad
            JOIN document_versions dv2 ON dv2.id = ad.document_version_id
            WHERE dv2.document_id = d.id
              AND ad.application_id = d.application_id
        )
      )
    ORDER BY d.id
    """
)

# Discover the actual foreign key on ``documents.application_id`` rather than assuming
# the PostgreSQL default name, so the drop is robust to naming conventions.
_FIND_APPLICATION_ID_FK = sa.text(
    """
    SELECT con.conname
    FROM pg_constraint con
    JOIN pg_attribute att
      ON att.attrelid = con.conrelid
     AND att.attnum = ANY (con.conkey)
    WHERE con.conrelid = 'documents'::regclass
      AND con.contype = 'f'
      AND att.attname = 'application_id'
    """
)


def upgrade() -> None:
    bind = op.get_bind()

    _assert_legacy_rows_preserved(bind)

    # Drop the legacy compatibility surface only after the invariant holds.
    fk_name = bind.execute(_FIND_APPLICATION_ID_FK).scalar_one_or_none()
    if fk_name is not None:
        op.drop_constraint(fk_name, "documents", type_="foreignkey")

    op.drop_index("ix_documents_application_id", table_name="documents")

    op.drop_column("documents", "application_id")
    op.drop_column("documents", "content")
    op.drop_column("documents", "content_json")
    op.drop_column("documents", "version")


def downgrade() -> None:
    raise RuntimeError(
        "Migration 0014 is forward-only and cannot be downgraded. The M5 document "
        "library is a many-to-many document/version/attachment history that cannot be "
        "losslessly reconstructed as the retired single-owner documents model. "
        "Recover by restoring a database snapshot taken before 0014 or by writing a "
        "forward corrective migration."
    )


def _assert_legacy_rows_preserved(bind: sa.engine.Connection) -> None:
    """Abort before any DDL if a legacy-owned document lacks M5 representation."""
    unpreserved = bind.execute(_PRESERVATION_QUERY).mappings().all()
    if unpreserved:
        offending = ", ".join(
            f"document {row['document_id']} (application {row['application_id']})"
            for row in unpreserved
        )
        raise RuntimeError(
            "Refusing to remove legacy documents compatibility columns: "
            f"{len(unpreserved)} legacy-owned document(s) lack a matching immutable "
            "document_versions payload and/or application_documents attachment and "
            f"would lose data: {offending}. Backfill the missing M5 representation "
            "before re-running migration 0014; no columns were dropped."
        )
