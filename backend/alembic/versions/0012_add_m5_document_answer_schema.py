"""Add M5 document/answer schema (additive, compatibility window).

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-19

Transforms the M1 placeholder ``documents`` table into the M5 reusable logical
document library and introduces the immutable ``document_versions``, append-only
``application_documents``, mutable ``answer_library``, and immutable
``application_answers`` tables described in
``docs/contracts/m5-packet-document-answer-contract.md``.

This migration is additive and preserves every existing ``documents`` row:

- It retains the legacy single-owner columns (``application_id`` cascade,
  ``content``, ``content_json``, ``version``) during the M5 compatibility window.
  A later PR removes them after readers switch.
- It reconciles legacy ``doc_type`` values to the canonical M5 vocabulary so the
  named ``CHECK`` constraint can be enforced, and backfills one logical document,
  one immutable initial version, and one application attachment per legacy row.

The deterministic backfill is reproducible and idempotent: version and attachment
IDs are derived with ``uuid5`` and inserted with ``ON CONFLICT DO NOTHING``.

``downgrade`` removes only the additive M5 schema/columns. The retained legacy
``application_id``/``content``/``content_json``/``version`` data is left intact; the
one-way ``doc_type`` reconciliation is not reversed.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

# Fixed namespace for deterministic, idempotent backfill identifiers.
_M5_NAMESPACE = uuid.UUID("0f7b9d2a-2f4c-5c7e-9d1a-7c8e5b3a4d6f")

_SEPARATORS = re.compile(r"[\s\-]+")
_RESUME_ALIASES = {"resume", "résumé", "resumé", "cv", "curriculum_vitae", "curriculumvitae"}
_COVER_LETTER_ALIASES = {
    "cover_letter",
    "coverletter",
    "cover",
    "cover_note",
    "covernote",
    "letter",
}
_DOC_TYPE_LABELS = {
    "resume": "Legacy resume",
    "cover_letter": "Legacy cover letter",
    "supporting": "Legacy supporting document",
    "other": "Legacy other document",
}


def upgrade() -> None:
    _add_logical_document_fields()
    _create_document_versions_table()
    _create_application_documents_table()
    _create_answer_library_table()
    _create_application_answers_table()
    _backfill_legacy_documents()
    _finalize_documents_constraints()


def downgrade() -> None:
    op.drop_constraint("ck_documents_name_not_blank_m5", "documents", type_="check")
    op.drop_constraint("ck_documents_doc_type_m5", "documents", type_="check")
    op.drop_index("ix_documents_is_archived", table_name="documents")
    op.drop_index("ix_documents_doc_type", table_name="documents")

    op.drop_table("application_answers")
    op.drop_table("answer_library")
    op.drop_table("application_documents")
    op.drop_table("document_versions")

    op.drop_column("documents", "updated_at")
    op.drop_column("documents", "is_archived")
    op.drop_column("documents", "name")


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

def _add_logical_document_fields() -> None:
    """Add the M5 logical-library fields to ``documents`` (name added nullable first)."""
    op.add_column("documents", sa.Column("name", sa.String(length=256), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def _create_document_versions_table() -> None:
    op.create_table(
        "document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "documents.id",
                ondelete="RESTRICT",
                name="fk_document_versions_document_id_documents",
            ),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_json", postgresql.JSONB(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "version_number > 0",
            name="ck_document_versions_version_positive_m5",
        ),
        sa.CheckConstraint(
            "content IS NOT NULL OR content_json IS NOT NULL",
            name="ck_document_versions_payload_present_m5",
        ),
    )
    op.create_index(
        "ix_document_versions_document_id", "document_versions", ["document_id"]
    )
    op.create_index(
        "ix_document_versions_checksum", "document_versions", ["checksum"]
    )
    op.create_index(
        "uq_document_versions_document_id_version_number_m5",
        "document_versions",
        ["document_id", "version_number"],
        unique=True,
    )


def _create_application_documents_table() -> None:
    op.create_table(
        "application_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "applications.id",
                ondelete="RESTRICT",
                name="fk_application_documents_application_id_applications",
            ),
            nullable=False,
        ),
        sa.Column(
            "document_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "document_versions.id",
                ondelete="RESTRICT",
                name="fk_application_documents_document_version_id_document_versions",
            ),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('resume', 'cover_letter', 'supporting', 'other')",
            name="ck_application_documents_role_m5",
        ),
        sa.CheckConstraint(
            "display_order >= 0",
            name="ck_application_documents_display_order_non_negative_m5",
        ),
    )
    op.create_index(
        "ix_application_documents_application_id",
        "application_documents",
        ["application_id"],
    )
    op.create_index(
        "ix_application_documents_document_version_id",
        "application_documents",
        ["document_version_id"],
    )
    op.create_index(
        "uq_application_documents_app_version_role_m5",
        "application_documents",
        ["application_id", "document_version_id", "role"],
        unique=True,
    )


def _create_answer_library_table() -> None:
    op.create_table(
        "answer_library",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_key", sa.String(length=256), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "question_key <> ''",
            name="ck_answer_library_question_key_not_blank_m5",
        ),
    )
    op.create_index(
        "ix_answer_library_question_key", "answer_library", ["question_key"]
    )
    op.create_index(
        "ix_answer_library_is_archived", "answer_library", ["is_archived"]
    )
    op.create_index(
        "uq_answer_library_question_key_active_m5",
        "answer_library",
        ["question_key"],
        unique=True,
        postgresql_where=sa.text("is_archived IS false"),
    )


def _create_application_answers_table() -> None:
    op.create_table(
        "application_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "applications.id",
                ondelete="RESTRICT",
                name="fk_application_answers_application_id_applications",
            ),
            nullable=False,
        ),
        sa.Column(
            "answer_library_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "answer_library.id",
                ondelete="RESTRICT",
                name="fk_application_answers_answer_library_id_answer_library",
            ),
            nullable=True,
        ),
        sa.Column("question_key", sa.String(length=256), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "question_key <> ''",
            name="ck_application_answers_question_key_not_blank_m5",
        ),
    )
    op.create_index(
        "ix_application_answers_application_id",
        "application_answers",
        ["application_id"],
    )
    op.create_index(
        "ix_application_answers_answer_library_id",
        "application_answers",
        ["answer_library_id"],
    )
    op.create_index(
        "uq_application_answers_app_question_key_m5",
        "application_answers",
        ["application_id", "question_key"],
        unique=True,
    )


def _finalize_documents_constraints() -> None:
    """Enforce the M5 ``documents`` constraints after the backfill populates ``name``."""
    op.alter_column("documents", "name", existing_type=sa.String(length=256), nullable=False)
    op.create_check_constraint(
        "ck_documents_doc_type_m5",
        "documents",
        "doc_type IN ('resume', 'cover_letter', 'supporting', 'other')",
    )
    op.create_check_constraint(
        "ck_documents_name_not_blank_m5",
        "documents",
        "name <> ''",
    )
    op.create_index("ix_documents_doc_type", "documents", ["doc_type"])
    op.create_index("ix_documents_is_archived", "documents", ["is_archived"])


# ---------------------------------------------------------------------------
# Deterministic legacy-document backfill
# ---------------------------------------------------------------------------

def _backfill_legacy_documents() -> None:
    """Create a logical document, initial version, and attachment per legacy row.

    Reproducible and idempotent: version/attachment IDs are derived with ``uuid5`` and
    inserted with ``ON CONFLICT DO NOTHING``; the logical-document upgrade only fills a
    null ``name`` and re-applies the deterministic ``doc_type``/``updated_at`` values.
    """
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT id, application_id, doc_type, content, content_json, version, created_at
            FROM documents
            ORDER BY created_at, id
            """
        )
    ).mappings().all()

    for row in rows:
        normalized_type = _normalize_doc_type(row["doc_type"])
        label = _DOC_TYPE_LABELS[normalized_type]
        version_number = _legacy_version_number(row["version"])
        content, content_json = _final_payload(
            row["content"], _as_json_object(row["content_json"])
        )
        checksum = _content_checksum(content, content_json)

        version_id = uuid.uuid5(
            _M5_NAMESPACE,
            f"document_version:{row['id']}:{version_number}",
        )
        attachment_id = uuid.uuid5(
            _M5_NAMESPACE,
            f"application_document:{row['application_id']}:{version_id}:{normalized_type}",
        )
        content_json_param = json.dumps(content_json) if content_json is not None else None

        bind.execute(
            sa.text(
                """
                UPDATE documents
                SET doc_type = :doc_type,
                    name = COALESCE(name, :name),
                    updated_at = :created_at
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {
                "doc_type": normalized_type,
                "name": label,
                "created_at": row["created_at"],
                "id": str(row["id"]),
            },
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO document_versions (
                    id, document_id, version_number, content, content_json, checksum, created_at
                )
                VALUES (
                    CAST(:id AS uuid),
                    CAST(:document_id AS uuid),
                    :version_number,
                    :content,
                    CAST(:content_json AS jsonb),
                    :checksum,
                    :created_at
                )
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": str(version_id),
                "document_id": str(row["id"]),
                "version_number": version_number,
                "content": content,
                "content_json": content_json_param,
                "checksum": checksum,
                "created_at": row["created_at"],
            },
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO application_documents (
                    id, application_id, document_version_id, role, display_order, created_at
                )
                VALUES (
                    CAST(:id AS uuid),
                    CAST(:application_id AS uuid),
                    CAST(:document_version_id AS uuid),
                    :role,
                    0,
                    :created_at
                )
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": str(attachment_id),
                "application_id": str(row["application_id"]),
                "document_version_id": str(version_id),
                "role": normalized_type,
                "created_at": row["created_at"],
            },
        )


def _normalize_doc_type(raw: str | None) -> str:
    """Reconcile a legacy ``doc_type`` to the canonical M5 vocabulary."""
    if raw is None:
        return "other"
    key = _SEPARATORS.sub("_", raw.strip().casefold()).strip("_")
    if key in _RESUME_ALIASES:
        return "resume"
    if key in _COVER_LETTER_ALIASES:
        return "cover_letter"
    if key == "supporting":
        return "supporting"
    return "other"


def _legacy_version_number(raw: object) -> int:
    """Preserve a positive legacy version; fall back to 1 for invalid values."""
    if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
        return raw
    return 1


def _final_payload(content: str | None, content_json: object) -> tuple[str | None, object]:
    """Preserve both payload fields; use empty text only when both are null."""
    if content is None and content_json is None:
        return "", None
    return content, content_json


def _as_json_object(value: object) -> object:
    """Return a Python object for ``content_json`` regardless of driver decoding."""
    if isinstance(value, str):
        return json.loads(value)
    return value


def _content_checksum(content: str | None, content_json: object) -> str:
    """SHA-256 of a UTF-8, sorted-key canonical JSON envelope of the final payload."""
    envelope = {"content": content, "content_json": content_json}
    canonical = json.dumps(
        envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
