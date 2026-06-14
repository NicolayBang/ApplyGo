"""Unit tests for deterministic application scoring."""

from applypilot.domain.applications.scoring import ApplicationScorer, JobScoringInput


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
    assert "Relevant technical keywords were found." in result.reasons
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
