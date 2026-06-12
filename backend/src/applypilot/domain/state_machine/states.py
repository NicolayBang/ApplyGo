"""Application state definitions for the M1 foundation."""

from enum import StrEnum


class ApplicationState(StrEnum):
    APPLICATION_CREATED = "ApplicationCreated"
    DRAFT = "Draft"
    READY_FOR_REVIEW = "ReadyForReview"
    APPROVED = "Approved"
    SUBMITTED = "Submitted"
    REJECTED = "Rejected"
    ARCHIVED = "Archived"
