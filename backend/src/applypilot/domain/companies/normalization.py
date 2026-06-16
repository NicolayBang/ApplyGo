"""Deterministic company identity normalization for M3."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

UNKNOWN_COMPANY_NAME = "Unknown Company"
CONFIDENTIAL_COMPANY_NAME = "Confidential Company"

_CONFIDENTIAL_MARKERS = (
    "confidential",
    "stealth",
    "undisclosed",
    "private employer",
    "private company",
)
_WHITESPACE_PATTERN = re.compile(r"\s+")
_NORMALIZED_NAME_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class CompanyIdentityCandidate:
    """Canonical company identity values before persistence."""

    name: str
    normalized_name: str
    domain: str | None = None
    normalized_domain: str | None = None
    placeholder: str | None = None


class CompanyIdentityNormalizer:
    """Normalize company identity without fuzzy matching or external lookups."""

    def normalize(
        self,
        company_text: str | None,
        *,
        company_domain: str | None = None,
    ) -> CompanyIdentityCandidate:
        """Return deterministic identity values for raw intake company text."""
        display_name = self._display_name(company_text)
        placeholder = self._placeholder(display_name)

        if placeholder == "unknown":
            display_name = UNKNOWN_COMPANY_NAME
        elif placeholder == "confidential":
            display_name = CONFIDENTIAL_COMPANY_NAME

        normalized_domain = self.normalize_domain(company_domain)
        return CompanyIdentityCandidate(
            name=display_name,
            normalized_name=self.normalize_name(display_name),
            domain=normalized_domain,
            normalized_domain=normalized_domain,
            placeholder=placeholder,
        )

    def normalize_name(self, value: str) -> str:
        """Normalize company names for deterministic exact-name matching."""
        compacted = self._display_name(value).casefold()
        normalized = _NORMALIZED_NAME_PATTERN.sub(" ", compacted)
        return _WHITESPACE_PATTERN.sub(" ", normalized).strip()

    def normalize_domain(self, value: str | None) -> str | None:
        """Normalize a direct company domain value.

        This intentionally accepts only an explicit company-domain value. Job posting URLs
        and ATS URLs must not be passed here as employer identity evidence.
        """
        if value is None:
            return None

        candidate = value.strip()
        if not candidate:
            return None

        parsed = urlparse(candidate if "://" in candidate else f"//{candidate}")
        host = (parsed.hostname or "").casefold().strip(".")
        if host.startswith("www."):
            host = host[4:]
        return host or None

    def _display_name(self, value: str | None) -> str:
        if value is None:
            return ""
        return _WHITESPACE_PATTERN.sub(" ", value).strip()

    def _placeholder(self, display_name: str) -> str | None:
        if not display_name:
            return "unknown"

        lowered = display_name.casefold()
        if any(marker in lowered for marker in _CONFIDENTIAL_MARKERS):
            return "confidential"
        return None

