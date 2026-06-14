"""Deterministic job intake classification for the M1 workflow."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from applypilot.domain.applications.models import JobCreate


@dataclass(frozen=True, slots=True)
class JobIntakeClassification:
    """Structured fields inferred from manual job intake."""

    job_type: str | None = None
    ats_type: str | None = None
    salary_raw: str | None = None
    remote_ok: bool = False


class JobIntakeClassifier:
    """Classify job metadata without LLM calls or external services."""

    _ATS_DOMAINS = {
        "ashbyhq.com": "ashby",
        "greenhouse.io": "greenhouse",
        "jobs.lever.co": "lever",
        "linkedin.com": "linkedin",
        "myworkdayjobs.com": "workday",
        "smartrecruiters.com": "smartrecruiters",
    }
    _ATS_TEXT_MARKERS = {
        "ashby": "ashby",
        "greenhouse": "greenhouse",
        "lever": "lever",
        "workday": "workday",
        "smartrecruiters": "smartrecruiters",
    }
    _JOB_TYPE_MARKERS = (
        ("contract", ("contract", "contractor", "freelance", "consultant")),
        ("internship", ("internship", "intern ", "co-op", "coop")),
        ("part-time", ("part-time", "part time")),
        ("temporary", ("temporary", "temp role", "seasonal")),
        ("full-time", ("full-time", "full time", "permanent")),
    )
    _LABELLED_SALARY_PATTERN = re.compile(
        r"(?:salary|compensation|pay|range)\s*[:\-]?\s*"
        r"(\$?\s?\d{2,3}(?:,\d{3})?(?:\s?[kK])?"
        r"(?:\s?(?:-|to|–)\s?\$?\s?\d{2,3}(?:,\d{3})?(?:\s?[kK])?)?"
        r"(?:\s?(?:CAD|USD|per year|annually|/year|/yr))?)"
    )
    _MONEY_SALARY_PATTERN = re.compile(
        r"(\$\s?\d{2,3}(?:,\d{3})?(?:\s?[kK])?"
        r"(?:\s?(?:-|to|–)\s?\$?\s?\d{2,3}(?:,\d{3})?(?:\s?[kK])?)?"
        r"(?:\s?(?:CAD|USD|per year|annually|/year|/yr))?)"
    )

    def enrich(self, data: JobCreate) -> JobCreate:
        """Return job data with blank classification fields filled."""
        classification = self.classify(data)
        update = data.model_dump()
        update["job_type"] = data.job_type or classification.job_type
        update["ats_type"] = data.ats_type or classification.ats_type
        update["salary_raw"] = data.salary_raw or classification.salary_raw
        update["remote_ok"] = data.remote_ok or classification.remote_ok
        return JobCreate(**update)

    def classify(self, data: JobCreate) -> JobIntakeClassification:
        searchable = self._searchable_text(data)
        return JobIntakeClassification(
            job_type=self._job_type(searchable),
            ats_type=self._ats_type(data.source_url, searchable),
            salary_raw=self._salary(searchable),
            remote_ok=self._remote_ok(data.location, searchable),
        )

    def _searchable_text(self, data: JobCreate) -> str:
        return " ".join(
            part
            for part in [
                data.title,
                data.company,
                data.location,
                data.source_url,
                data.raw_text,
            ]
            if part
        ).strip()

    def _job_type(self, text: str) -> str | None:
        lowered = f" {text.lower()} "
        for job_type, markers in self._JOB_TYPE_MARKERS:
            if any(marker in lowered for marker in markers):
                return job_type
        return None

    def _ats_type(self, source_url: str | None, text: str) -> str | None:
        if source_url:
            host = urlparse(source_url).netloc.lower()
            for domain, ats_type in self._ATS_DOMAINS.items():
                if domain in host:
                    return ats_type

        lowered = text.lower()
        for marker, ats_type in self._ATS_TEXT_MARKERS.items():
            if marker in lowered:
                return ats_type
        return None

    def _salary(self, text: str) -> str | None:
        match = self._LABELLED_SALARY_PATTERN.search(text)
        if match is None:
            match = self._MONEY_SALARY_PATTERN.search(text)
        if match is None:
            return None
        return " ".join(match.group(1).split())

    def _remote_ok(self, location: str | None, text: str) -> bool:
        searchable = " ".join(part for part in [location, text] if part).lower()
        return "remote" in searchable or "work from home" in searchable
