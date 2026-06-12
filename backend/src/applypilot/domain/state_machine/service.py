"""State machine helper for validating and applying transitions."""

from applypilot.domain.state_machine.states import ApplicationState
from applypilot.domain.state_machine.transitions import ALLOWED_TRANSITIONS


class InvalidStateTransitionError(ValueError):
    """Raised when a state transition is not allowed by the machine."""


class ApplicationStateMachine:
    """Small helper that enforces configured transition rules."""

    def can_transition(self, current: ApplicationState, target: ApplicationState) -> bool:
        return target in ALLOWED_TRANSITIONS.get(current, set())

    def next_states(self, current: ApplicationState) -> set[ApplicationState]:
        return ALLOWED_TRANSITIONS.get(current, set()).copy()

    def apply_transition(
        self,
        current: ApplicationState,
        target: ApplicationState,
    ) -> ApplicationState:
        if not self.can_transition(current, target):
            raise InvalidStateTransitionError(
                f"Invalid transition: {current.value} -> {target.value}"
            )
        return target