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

    # Admin can approve pending_admin_approval -> approved
    assert validate_transition("pending_admin_approval", "approved", ["admin"]) is True
    
    # Manager can route pending_manager_routing -> routed
    assert validate_transition("pending_manager_routing", "routed", ["manager"]) is True

    # Admin can execute approved -> resolved
    assert validate_transition("approved", "resolved", ["admin"]) is True

    # Agent can transition open -> pending_admin_approval
    assert validate_transition("open", "pending_admin_approval", ["agent"]) is True


def test_invalid_arbitrary_transitions():
    # draft -> resolved is never allowed
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("draft", "resolved", ["admin"])

    # User/Agent cannot transition pending_admin_approval -> approved
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("pending_admin_approval", "approved", ["user"])
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("pending_admin_approval", "approved", ["agent"])

    # User/Agent cannot transition pending_manager_routing -> routed
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("pending_manager_routing", "routed", ["user"])
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("pending_manager_routing", "routed", ["agent"])


def test_available_transitions_query():
    user_transitions = get_available_transitions("open", ["user"])
    assert "cancelled" in user_transitions
    assert "assigned" not in user_transitions

    agent_transitions = get_available_transitions("open", ["agent"])
    assert "assigned" in agent_transitions
    assert "pending_admin_approval" in agent_transitions

