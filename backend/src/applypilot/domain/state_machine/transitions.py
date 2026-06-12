"""Allowed state transitions for the application state machine."""

from applypilot.domain.state_machine.states import ApplicationState


ALLOWED_TRANSITIONS: dict[ApplicationState, set[ApplicationState]] = {
    ApplicationState.APPLICATION_CREATED: {ApplicationState.DRAFT},
    ApplicationState.DRAFT: {
        ApplicationState.READY_FOR_REVIEW,
        ApplicationState.ARCHIVED,
    },
    ApplicationState.READY_FOR_REVIEW: {
        ApplicationState.APPROVED,
        ApplicationState.REJECTED,
        ApplicationState.DRAFT,
    },
    ApplicationState.APPROVED: {
        ApplicationState.SUBMITTED,
        ApplicationState.REJECTED,
    },
    ApplicationState.SUBMITTED: {ApplicationState.ARCHIVED},
    ApplicationState.REJECTED: {ApplicationState.ARCHIVED},
    ApplicationState.ARCHIVED: set(),
}