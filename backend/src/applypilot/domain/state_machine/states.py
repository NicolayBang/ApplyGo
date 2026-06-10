"""Placeholder workflow states for milestone 1."""

from enum import StrEnum


class ApplicationState(StrEnum):
    DISCOVERED = "discovered"
    PARSED = "parsed"
    SCORED = "scored"
    PACKET_READY = "packet_ready"
    REVIEW_NEEDED = "review_needed"
    FORM_FILLED = "form_filled"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    INTERVIEW = "interview"
    CLOSED = "closed"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    FAILED_RETRYABLE = "failed_retryable"
