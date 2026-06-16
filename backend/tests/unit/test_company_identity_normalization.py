"""Unit tests for deterministic M3 company identity normalization."""

from applypilot.domain.companies.normalization import (
    CONFIDENTIAL_COMPANY_NAME,
    UNKNOWN_COMPANY_NAME,
    CompanyIdentityNormalizer,
)


def test_blank_company_maps_to_unknown_placeholder() -> None:
    candidate = CompanyIdentityNormalizer().normalize("   ")

    assert candidate.name == UNKNOWN_COMPANY_NAME
    assert candidate.normalized_name == "unknown company"
    assert candidate.domain is None
    assert candidate.normalized_domain is None
    assert candidate.placeholder == "unknown"


def test_confidential_company_maps_to_confidential_placeholder() -> None:
    candidate = CompanyIdentityNormalizer().normalize("Confidential employer")

    assert candidate.name == CONFIDENTIAL_COMPANY_NAME
    assert candidate.normalized_name == "confidential company"
    assert candidate.placeholder == "confidential"


def test_company_name_normalization_is_exact_and_deterministic() -> None:
    normalizer = CompanyIdentityNormalizer()

    first = normalizer.normalize("  ApplyPilot,   Inc. ")
    second = normalizer.normalize("applypilot inc")

    assert first.name == "ApplyPilot, Inc."
    assert first.normalized_name == "applypilot inc"
    assert second.normalized_name == first.normalized_name


def test_direct_company_domain_is_normalized_without_source_url_inference() -> None:
    candidate = CompanyIdentityNormalizer().normalize(
        "ApplyPilot",
        company_domain="https://www.ApplyPilot.com/careers?job=1",
    )

    assert candidate.domain == "applypilot.com"
    assert candidate.normalized_domain == "applypilot.com"


def test_normalizer_has_no_job_source_url_input() -> None:
    candidate = CompanyIdentityNormalizer().normalize(
        "Example Co",
        company_domain=None,
    )

    assert candidate.name == "Example Co"
    assert candidate.normalized_name == "example co"
    assert candidate.domain is None
    assert candidate.normalized_domain is None
    assert candidate.placeholder is None
