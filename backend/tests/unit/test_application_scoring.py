"""Unit tests for deterministic application scoring."""

import uuid

from applypilot.domain.applications.intake import JobIntakeClassifier
from applypilot.domain.applications.models import JobCreate
from applypilot.domain.applications.scoring import ApplicationScorer, JobScoringInput
from applypilot.domain.policy import (
    AutomationMode,
    ConfidenceLevel,
    PolicyContext,
    PolicyDecisionOutcome,
    PolicyEngine,
    PolicyRequest,
    WorkerType,
)


def test_scorer_recommends_complete_technical_remote_job() -> None:
    result = ApplicationScorer().score(
        JobScoringInput(
            title="Backend Platform Engineer",
            company="ApplyPilot",
            location="Remote",
            source_url="https://example.com/jobs/backend-platform-engineer",
            raw_text=(
                "Build Python APIs with FastAPI, PostgreSQL, automation workflows, "
                "and platform data services for internal users. Partner with DevOps "
                "and product teams to improve reliable backend delivery."
            ),
            remote_ok=True,
            job_type="full-time",
            ats_type="lever",
            salary_raw="$95,000 - $125,000",
        )
    )

    assert result.fit_score >= 75
    assert result.confidence == "high"
    assert result.recommendation == "recommended"
    assert result.missing_data == []
    assert "Relevant technical keywords were found:" in " ".join(result.reasons)
    assert "python" in " ".join(result.reasons)
    assert "Job type was classified for screening." in result.reasons
    assert "ATS source was classified for traceability." in result.reasons
    assert "Compensation information is available for review." in result.reasons


def test_scorer_flags_sparse_job_for_review() -> None:
    result = ApplicationScorer().score(
        JobScoringInput(
            title="Role",
            company=None,
            raw_text=None,
        )
    )

    assert result.confidence == "low"
    assert result.recommendation == "needs_review"
    assert "company" in result.missing_data
    assert "detailed job description" in result.missing_data
    assert "job type" in result.missing_data
    assert "compensation range" in result.missing_data
    assert "Limited job description reduces screening confidence." in result.risks
    assert "Compensation is missing and should be confirmed before applying." in result.risks


def test_scorer_marks_compensation_red_flag_not_recommended() -> None:
    result = ApplicationScorer().score(
        JobScoringInput(
            title="Junior Developer",
            company="Example Co",
            source_url="https://example.com/job",
            raw_text="This is an unpaid commission only developer role with backend API work.",
            remote_ok=True,
        )
    )

    assert result.confidence == "low"
    assert result.recommendation == "not_recommended"
    assert result.red_flags == ["Compensation language needs review."]


def test_scorer_uses_classified_metadata_without_external_services() -> None:
    result = ApplicationScorer().score(
        JobScoringInput(
            title="Backend Developer",
            company="Example Co",
            source_url="https://jobs.lever.co/example/backend-developer",
            raw_text="Build Python APIs and backend automation.",
            job_type="contract",
            ats_type="lever",
            salary_raw="$80k to $95k",
        )
    )

    assert result.fit_score >= 70
    assert "Job type was classified for screening." in result.reasons
    assert "ATS source was classified for traceability." in result.reasons
    assert "Compensation information is available for review." in result.reasons
    assert "job type" not in result.missing_data
    assert "compensation range" not in result.missing_data


def test_scorer_flags_unclassified_source_when_url_is_present() -> None:
    result = ApplicationScorer().score(
        JobScoringInput(
            title="Backend Developer",
            company="Example Co",
            source_url="https://example.com/job",
            raw_text=(
                "Build backend APIs with Python and SQL for reliable internal data workflows. "
                "Work with platform teams on automation services and operational tooling."
            ),
            job_type="full-time",
            salary_raw="$85k to $110k",
        )
    )

    assert "ATS/source type was not classified from the posting URL or text." in result.risks


def test_dashboard_sample_job_scores_high_and_allows_dry_run_policy() -> None:
    """The live dashboard sample carries enough deterministic data for the M1 demo path."""
    job = JobIntakeClassifier().enrich(
        JobCreate(
            title="Backend Platform Engineer",
            company="ApplyPilot Demo Co.",
            location="Remote",
            source_url="https://jobs.lever.co/applypilot/backend-platform-engineer",
            raw_text=(
                "Build Python APIs with FastAPI, PostgreSQL, automation workflows, and "
                "platform data services. This is a full-time remote role with a salary "
                "range of $95,000 - $125,000. Partner with DevOps and product teams to "
                "improve reliable backend delivery."
            ),
            remote_ok=True,
        )
    )

    score = ApplicationScorer().score(JobScoringInput(**job.model_dump()))
    decision = PolicyEngine().evaluate(
        PolicyRequest(
            application_id=uuid.uuid4(),
            current_state="Approved",
            requested_action="send_follow_up_email",
            worker=WorkerType.EMAIL,
            context=PolicyContext(
                confidence=ConfidenceLevel(score.confidence),
                fit_score=score.fit_score,
                recommendation=score.recommendation,
                reasons=score.reasons,
                risks=score.risks,
                missing_data=score.missing_data,
                red_flags=score.red_flags,
            ),
            mode=AutomationMode.DRY_RUN,
        )
    )

    assert job.job_type == "full-time"
    assert job.ats_type == "lever"
    assert job.salary_raw == "$95,000 - $125,000"
    assert score.confidence == "high"
    assert score.missing_data == []
    assert decision.decision == PolicyDecisionOutcome.ALLOW
    assert decision.allowed is True
