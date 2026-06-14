"""Unit tests for governed policy evaluation rules."""

import uuid

from applypilot.domain.policy import (
    AutomationMode,
    ConfidenceLevel,
    PolicyContext,
    PolicyDecisionOutcome,
    PolicyEngine,
    PolicyRequest,
    WorkerType,
)


def make_request(
    *,
    mode: AutomationMode,
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
    fit_score: int | None = None,
    recommendation: str | None = None,
    risks: list[str] | None = None,
    missing_data: list[str] | None = None,
    red_flags: list[str] | None = None,
) -> PolicyRequest:
    return PolicyRequest(
        application_id=uuid.uuid4(),
        current_state="Approved",
        requested_action="send_follow_up_email",
        worker=WorkerType.EMAIL,
        context=PolicyContext(
            confidence=confidence,
            fit_score=fit_score,
            recommendation=recommendation,
            risks=risks or [],
            missing_data=missing_data or [],
            red_flags=red_flags or [],
        ),
        mode=mode,
    )


def test_low_confidence_forces_review_in_full_auto() -> None:
    decision = PolicyEngine().evaluate(
        make_request(mode=AutomationMode.FULL_AUTO, confidence=ConfidenceLevel.LOW)
    )

    assert decision.decision == PolicyDecisionOutcome.REVIEW
    assert decision.allowed is False
    assert decision.required_overrides == ["human_review"]


def test_manual_mode_requires_human_approval() -> None:
    decision = PolicyEngine().evaluate(make_request(mode=AutomationMode.MANUAL))

    assert decision.decision == PolicyDecisionOutcome.REVIEW
    assert decision.required_overrides == ["human_approval"]


def test_dry_run_allows_planning_without_side_effects() -> None:
    decision = PolicyEngine().evaluate(make_request(mode=AutomationMode.DRY_RUN))

    assert decision.decision == PolicyDecisionOutcome.ALLOW
    assert decision.allowed is True
    assert "must not create side effects" in decision.reasons[0]


def test_full_auto_denies_red_flags() -> None:
    decision = PolicyEngine().evaluate(
        make_request(mode=AutomationMode.FULL_AUTO, red_flags=["external site mismatch"])
    )

    assert decision.decision == PolicyDecisionOutcome.DENY
    assert decision.allowed is False
    assert decision.required_overrides == ["manual_override"]


def test_full_auto_denies_not_recommended_score() -> None:
    decision = PolicyEngine().evaluate(
        make_request(
            mode=AutomationMode.FULL_AUTO,
            fit_score=42,
            recommendation="not_recommended",
        )
    )

    assert decision.decision == PolicyDecisionOutcome.DENY
    assert decision.allowed is False
    assert decision.required_overrides == ["manual_override"]


def test_dry_run_requires_review_for_not_recommended_score() -> None:
    decision = PolicyEngine().evaluate(
        make_request(
            mode=AutomationMode.DRY_RUN,
            fit_score=42,
            recommendation="not_recommended",
        )
    )

    assert decision.decision == PolicyDecisionOutcome.REVIEW
    assert decision.allowed is False
    assert decision.required_overrides == ["human_review"]


def test_semi_auto_requires_review_for_low_fit_score() -> None:
    decision = PolicyEngine().evaluate(
        make_request(mode=AutomationMode.SEMI_AUTO, fit_score=40)
    )

    assert decision.decision == PolicyDecisionOutcome.REVIEW
    assert decision.required_overrides == ["score_review"]


def test_semi_auto_requires_review_for_missing_data() -> None:
    decision = PolicyEngine().evaluate(
        make_request(mode=AutomationMode.SEMI_AUTO, missing_data=["recruiter email"])
    )

    assert decision.decision == PolicyDecisionOutcome.REVIEW
    assert decision.required_overrides == ["complete_missing_data"]


def test_semi_auto_allows_clear_medium_confidence_request() -> None:
    decision = PolicyEngine().evaluate(
        make_request(mode=AutomationMode.SEMI_AUTO, confidence=ConfidenceLevel.MEDIUM)
    )

    assert decision.decision == PolicyDecisionOutcome.ALLOW
    assert decision.allowed is True
