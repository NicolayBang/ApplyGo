"""Deterministic policy engine for governed automation modes."""

from applypilot.domain.policy.models import (
    AutomationMode,
    ConfidenceLevel,
    PolicyDecision,
    PolicyDecisionOutcome,
    PolicyRequest,
)


class PolicyEngine:
    """Evaluate whether an automation action may proceed, needs review, or is denied."""

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        context = request.context

        if context.confidence == ConfidenceLevel.LOW:
            return self._review(
                request.mode,
                "Low-confidence outcomes require human review.",
                required_overrides=["human_review"],
            )

        if context.red_flags:
            if request.mode == AutomationMode.FULL_AUTO:
                return self._deny(
                    request.mode,
                    "Red flags block full-auto execution.",
                    required_overrides=["manual_override"],
                )
            return self._review(
                request.mode,
                "Red flags require human review before execution.",
                required_overrides=["human_review"],
            )

        if context.recommendation == "not_recommended":
            if request.mode == AutomationMode.FULL_AUTO:
                return self._deny(
                    request.mode,
                    "Not-recommended applications block full-auto execution.",
                    required_overrides=["manual_override"],
                )
            return self._review(
                request.mode,
                "Not-recommended applications require human review.",
                required_overrides=["human_review"],
            )

        if context.fit_score is not None and context.fit_score < 45:
            return self._review(
                request.mode,
                "Low fit scores require human review before execution.",
                required_overrides=["score_review"],
            )

        if request.mode == AutomationMode.MANUAL:
            return self._review(
                request.mode,
                "Manual mode requires human approval before execution.",
                required_overrides=["human_approval"],
            )

        if context.missing_data:
            return self._review(
                request.mode,
                "Missing data requires review before execution.",
                required_overrides=["complete_missing_data"],
            )

        if context.risks and request.mode != AutomationMode.DRY_RUN:
            return self._review(
                request.mode,
                "Identified risks require review before execution.",
                required_overrides=["risk_review"],
            )

        if request.mode == AutomationMode.DRY_RUN:
            return self._allow(
                request.mode,
                "Dry-run mode may plan the action but must not create side effects.",
            )

        return self._allow(request.mode, "Policy checks passed.")

    def _allow(self, mode: AutomationMode, reason: str) -> PolicyDecision:
        return PolicyDecision(
            decision=PolicyDecisionOutcome.ALLOW,
            mode=mode,
            reasons=[reason],
        )

    def _review(
        self,
        mode: AutomationMode,
        reason: str,
        *,
        required_overrides: list[str],
    ) -> PolicyDecision:
        return PolicyDecision(
            decision=PolicyDecisionOutcome.REVIEW,
            mode=mode,
            reasons=[reason],
            required_overrides=required_overrides,
        )

    def _deny(
        self,
        mode: AutomationMode,
        reason: str,
        *,
        required_overrides: list[str],
    ) -> PolicyDecision:
        return PolicyDecision(
            decision=PolicyDecisionOutcome.DENY,
            mode=mode,
            reasons=[reason],
            required_overrides=required_overrides,
        )
