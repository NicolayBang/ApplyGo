"""Unit tests for M1 application state machine rules."""

import pytest

from applypilot.domain.state_machine import (
    ApplicationState,
    ApplicationStateMachine,
    InvalidStateTransitionError,
)


def test_valid_transition_application_created_to_draft() -> None:
    machine = ApplicationStateMachine()

    result = machine.apply_transition(
        ApplicationState.APPLICATION_CREATED,
        ApplicationState.DRAFT,
    )

    assert result == ApplicationState.DRAFT


def test_valid_transition_draft_to_ready_for_review() -> None:
    machine = ApplicationStateMachine()

    result = machine.apply_transition(
        ApplicationState.DRAFT,
        ApplicationState.READY_FOR_REVIEW,
    )

    assert result == ApplicationState.READY_FOR_REVIEW


def test_valid_transition_ready_for_review_to_approved() -> None:
    machine = ApplicationStateMachine()

    result = machine.apply_transition(
        ApplicationState.READY_FOR_REVIEW,
        ApplicationState.APPROVED,
    )

    assert result == ApplicationState.APPROVED


def test_valid_transition_approved_to_submitted() -> None:
    machine = ApplicationStateMachine()

    result = machine.apply_transition(
        ApplicationState.APPROVED,
        ApplicationState.SUBMITTED,
    )

    assert result == ApplicationState.SUBMITTED


def test_valid_transition_rejected_to_archived() -> None:
    machine = ApplicationStateMachine()

    result = machine.apply_transition(
        ApplicationState.REJECTED,
        ApplicationState.ARCHIVED,
    )

    assert result == ApplicationState.ARCHIVED


def test_invalid_transition_draft_to_submitted_rejected() -> None:
    machine = ApplicationStateMachine()

    with pytest.raises(InvalidStateTransitionError):
        machine.apply_transition(ApplicationState.DRAFT, ApplicationState.SUBMITTED)


def test_invalid_transition_archived_to_draft_rejected() -> None:
    machine = ApplicationStateMachine()

    with pytest.raises(InvalidStateTransitionError):
        machine.apply_transition(ApplicationState.ARCHIVED, ApplicationState.DRAFT)
