"""Unit tests for M3 company read compatibility projection."""

from datetime import datetime, timezone
from types import SimpleNamespace
import uuid

from applypilot.domain.applications.models import JobRead


def test_job_read_projects_canonical_company_and_source_text() -> None:
    company_id = uuid.uuid4()
    job = SimpleNamespace(
        id=uuid.uuid4(),
        source_url=None,
        raw_text=None,
        title="Backend Engineer",
        company="ApplyPilot, Inc.",
        company_id=company_id,
        company_identity=SimpleNamespace(name="ApplyPilot"),
        location="Remote",
        remote_ok=True,
        job_type="full-time",
        ats_type=None,
        salary_raw=None,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )

    result = JobRead.model_validate(job)

    assert result.company == "ApplyPilot"
    assert result.company_source_text == "ApplyPilot, Inc."
    assert result.company_id == company_id


def test_job_read_falls_back_to_source_text_without_company_identity() -> None:
    job = SimpleNamespace(
        id=uuid.uuid4(),
        source_url=None,
        raw_text=None,
        title="Mystery Role",
        company=None,
        company_id=None,
        company_identity=None,
        location=None,
        remote_ok=False,
        job_type=None,
        ats_type=None,
        salary_raw=None,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )

    result = JobRead.model_validate(job)

    assert result.company is None
    assert result.company_source_text is None
    assert result.company_id is None
