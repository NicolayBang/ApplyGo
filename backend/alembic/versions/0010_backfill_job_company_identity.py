"""Backfill job company identity.

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-15
"""

from __future__ import annotations

import re
import uuid

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

_COMPANY_NAMESPACE = uuid.UUID("6e774dcb-6be4-4d88-b455-a0f968f7524c")
_CONFIDENTIAL_MARKERS = (
    "confidential",
    "stealth",
    "undisclosed",
    "private employer",
    "private company",
)
_WHITESPACE_PATTERN = re.compile(r"\s+")
_NORMALIZED_NAME_PATTERN = re.compile(r"[^a-z0-9]+")


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT id, company
            FROM jobs
            WHERE company_id IS NULL
            ORDER BY created_at, id
            """
        )
    ).mappings()

    for row in rows:
        candidate = _company_candidate(row["company"])
        company_id = _resolve_company(bind, candidate)
        bind.execute(
            sa.text(
                """
                UPDATE jobs
                SET company_id = CAST(:company_id AS uuid)
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {"company_id": str(company_id), "job_id": str(row["id"])},
        )


def downgrade() -> None:
    op.execute("UPDATE jobs SET company_id = NULL")


def _company_candidate(company_text: str | None) -> dict[str, str]:
    display_name = _display_name(company_text)
    placeholder = _placeholder(display_name)

    if placeholder == "unknown":
        display_name = "Unknown Company"
    elif placeholder == "confidential":
        display_name = "Confidential Company"

    return {
        "name": display_name,
        "normalized_name": _normalize_name(display_name),
    }


def _resolve_company(bind, candidate: dict[str, str]) -> uuid.UUID:
    existing = bind.execute(
        sa.text(
            """
            SELECT id
            FROM companies
            WHERE normalized_domain IS NULL
              AND normalized_name = :normalized_name
            LIMIT 1
            """
        ),
        {"normalized_name": candidate["normalized_name"]},
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    company_id = uuid.uuid5(
        _COMPANY_NAMESPACE,
        f"company:no-domain:{candidate['normalized_name']}",
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO companies (
                id,
                name,
                normalized_name,
                domain,
                normalized_domain
            )
            VALUES (
                CAST(:company_id AS uuid),
                :name,
                :normalized_name,
                NULL,
                NULL
            )
            """
        ),
        {
            "company_id": str(company_id),
            "name": candidate["name"],
            "normalized_name": candidate["normalized_name"],
        },
    )
    return company_id


def _display_name(value: str | None) -> str:
    if value is None:
        return ""
    return _WHITESPACE_PATTERN.sub(" ", value).strip()


def _normalize_name(value: str) -> str:
    normalized = _NORMALIZED_NAME_PATTERN.sub(" ", _display_name(value).casefold())
    return _WHITESPACE_PATTERN.sub(" ", normalized).strip()


def _placeholder(display_name: str) -> str | None:
    if not display_name:
        return "unknown"

    lowered = display_name.casefold()
    if any(marker in lowered for marker in _CONFIDENTIAL_MARKERS):
        return "confidential"
    return None
