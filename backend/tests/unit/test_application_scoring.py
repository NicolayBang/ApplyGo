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
        )
    )

    assert result.fit_score >= 75
    assert result.confidence == "high"
    assert result.recommendation == "recommended"
    assert result.missing_data == []
    assert "Relevant technical keywords were found." in result.reasons


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
