"""Unit tests for deterministic job intake classification."""

from applypilot.domain.applications.intake import JobIntakeClassifier
from applypilot.domain.applications.models import JobCreate


def test_classifier_extracts_job_type_ats_salary_and_remote_marker() -> None:
    result = JobIntakeClassifier().classify(
        JobCreate(
            title="Backend Platform Engineer",
            company="Example Co",
            location="Canada Remote",
            source_url="https://jobs.lever.co/example/backend-platform-engineer",
            raw_text=(
                "Full-time role building Python APIs. Compensation: "
                "$95,000 - $125,000 CAD annually."
            ),
        )
    )

    assert result.job_type == "full-time"
    assert result.ats_type == "lever"
    assert result.salary_raw == "$95,000 - $125,000 CAD"
    assert result.remote_ok is True


def test_enrich_preserves_human_provided_classification_values() -> None:
    enriched = JobIntakeClassifier().enrich(
        JobCreate(
            title="Part-time Developer",
            source_url="https://boards.greenhouse.io/example/jobs/123",
            raw_text="Compensation: $80k to $90k. Remote.",
            job_type="contract",
            ats_type="custom",
            salary_raw="Human-entered salary note",
            remote_ok=False,
        )
    )

    assert enriched.job_type == "contract"
    assert enriched.ats_type == "custom"
    assert enriched.salary_raw == "Human-entered salary note"
    assert enriched.remote_ok is True


def test_classifier_returns_blank_fields_for_sparse_intake() -> None:
    result = JobIntakeClassifier().classify(JobCreate(title="General role"))

    assert result.job_type is None
    assert result.ats_type is None
    assert result.salary_raw is None
    assert result.remote_ok is False


def test_classifier_does_not_treat_url_numbers_as_salary() -> None:
    result = JobIntakeClassifier().classify(
        JobCreate(
            title="Developer",
            source_url="https://boards.greenhouse.io/example/jobs/123456",
        )
    )

    assert result.ats_type == "greenhouse"
    assert result.salary_raw is None
