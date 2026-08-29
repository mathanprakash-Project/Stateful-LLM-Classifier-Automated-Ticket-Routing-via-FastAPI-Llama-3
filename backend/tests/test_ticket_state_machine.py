"""
Tests for the Ticket State Machine and transition permissions.
"""

import pytest
from app.core.exceptions import InvalidStateTransitionError
from app.core.ticket_state_machine import validate_transition, get_available_transitions


def test_valid_transitions_by_role():
    # User can transition draft -> open
    assert validate_transition("draft", "open", ["user"]) is True

    # User cannot transition open -> assigned
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("open", "assigned", ["user"])

    # Agent can transition open -> assigned
    assert validate_transition("open", "assigned", ["agent"]) is True

    # Agent can transition assigned -> in_progress
    assert validate_transition("assigned", "in_progress", ["agent"]) is True

    # Agent can transition in_progress -> resolved
    assert validate_transition("in_progress", "resolved", ["agent"]) is True

    # Manager can transition in_progress -> escalated
    assert validate_transition("in_progress", "escalated", ["manager"]) is True


def test_invalid_arbitrary_transitions():
    # draft -> resolved is never allowed
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("draft", "resolved", ["admin"])


def test_available_transitions_query():
    user_transitions = get_available_transitions("open", ["user"])
    assert "cancelled" in user_transitions
    assert "assigned" not in user_transitions

    agent_transitions = get_available_transitions("open", ["agent"])
    assert "assigned" in agent_transitions

