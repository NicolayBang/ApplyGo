"""Placeholder models for jobs, applications, documents, and related records."""

from dataclasses import dataclass


@dataclass(slots=True)
class ApplicationRecord:
    """Minimal placeholder for the canonical application record."""

    application_id: str
