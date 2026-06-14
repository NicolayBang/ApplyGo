"""Deterministic application scoring for the M1 workflow."""

from __future__ import annotations

from dataclasses import dataclass

from applypilot.domain.applications.models import ScoringResult


@dataclass(frozen=True, slots=True)
class JobScoringInput:
    """Normalized job fields used by the deterministic scorer."""

    title: str | None = None
    company: str | None = None
    location: str | None = None
    source_url: str | None = None
    raw_text: str | None = None
    remote_ok: bool = False
    job_type: str | None = None
    ats_type: str | None = None
    salary_raw: str | None = None


class ApplicationScorer:
    """Score application readiness without LLMs or external services."""

    _TECHNICAL_KEYWORDS = {
        "api",
        "automation",
        "backend",
        "data",
        "devops",
        "fastapi",
        "platform",
        "postgres",
        "python",
        "sql",
    }

    def score(self, job: JobScoringInput) -> ScoringResult:
        score = 40
        reasons: list[str] = []
        risks: list[str] = []
        missing_data: list[str] = []
        red_flags: list[str] = []

        if job.title:
            score += 15
            reasons.append("Role title is available for review.")
        else:
            missing_data.append("role title")

        if job.company:
            score += 10
            reasons.append("Company is identified.")
        else:
            missing_data.append("company")

        if job.source_url:
            score += 5
            reasons.append("Source URL is available for traceability.")
        else:
            missing_data.append("job source URL")

        if job.raw_text and len(job.raw_text.strip()) >= 120:
            score += 15
            reasons.append("Job description has enough detail for screening.")
        else:
            missing_data.append("detailed job description")

        if job.remote_ok:
            score += 5
            reasons.append("Remote compatibility is marked.")

        if job.job_type:
            score += 5
            reasons.append("Job type was classified for screening.")
        else:
            missing_data.append("job type")

        if job.ats_type:
            reasons.append("ATS source was classified for traceability.")

        if job.salary_raw:
            score += 5
            reasons.append("Compensation information is available for review.")
        else:
            missing_data.append("compensation range")

        searchable_text = " ".join(
            part
            for part in [
                job.title,
                job.company,
                job.location,
                job.raw_text,
                job.job_type,
                job.ats_type,
                job.salary_raw,
            ]
            if part
        ).lower()
        matched_keywords = sorted(
            keyword for keyword in self._TECHNICAL_KEYWORDS if keyword in searchable_text
        )
        if matched_keywords:
            score += min(10, len(matched_keywords) * 2)
            reasons.append("Relevant technical keywords were found.")

        if "senior" in searchable_text or "lead" in searchable_text:
            risks.append("Seniority expectations should be reviewed by a human.")

        if "unpaid" in searchable_text or "commission only" in searchable_text:
            red_flags.append("Compensation language needs review.")

        score = max(0, min(score, 100))
        confidence = self._confidence(score, missing_data, red_flags)
        recommendation = self._recommendation(score, red_flags)

        return ScoringResult(
            fit_score=score,
            confidence=confidence,
            recommendation=recommendation,
            reasons=reasons,
            risks=risks,
            missing_data=missing_data,
            red_flags=red_flags,
        )

    def _confidence(self, score: int, missing_data: list[str], red_flags: list[str]) -> str:
        if red_flags or score < 50 or len(missing_data) >= 3:
            return "low"
        if score >= 75 and not missing_data:
            return "high"
        return "medium"

    def _recommendation(self, score: int, red_flags: list[str]) -> str:
        if red_flags or score < 45:
            return "not_recommended"
        if score >= 75:
            return "recommended"
        return "needs_review"
