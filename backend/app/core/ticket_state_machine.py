"""
Ticket state machine with role-based transition validation.
"""

from typing import Dict, List, Set, Tuple
from app.core.constants import TicketStatus, UserRole
from app.core.exceptions import InvalidStateTransitionError

# (from_status, to_status) -> allowed_roles
ALLOWED_TRANSITIONS: Dict[Tuple[str, str], Set[str]] = {
    ("draft", "open"): {UserRole.USER.value, UserRole.ADMIN.value},
    ("draft", "cancelled"): {UserRole.USER.value, UserRole.ADMIN.value},
    ("open", "assigned"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("open", "in_progress"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},  # direct pick up
    ("open", "cancelled"): {UserRole.USER.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("assigned", "in_progress"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("assigned", "open"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("assigned", "cancelled"): {UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("in_progress", "resolved"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("in_progress", "escalated"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("in_progress", "assigned"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("escalated", "in_progress"): {UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("escalated", "resolved"): {UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("resolved", "closed"): {UserRole.USER.value, UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("resolved", "reopened"): {UserRole.USER.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("closed", "reopened"): {UserRole.USER.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    # Manager routing flow
    ("open", "pending_manager_routing"): {"agent", "manager", "admin"},
    ("pending_manager_routing", "routed"): {"manager", "admin"},
    ("pending_manager_routing", "assigned"): {"agent", "manager", "admin"},
    ("pending_manager_routing", "open"): {"manager", "admin"},
    ("pending_manager_routing", "rejected"): {"manager", "admin"},
    ("pending_manager_routing", "cancelled"): {"manager", "admin"},
    ("routed", "in_progress"): {"agent", "manager", "admin"},
    ("routed", "resolved"): {"agent", "manager", "admin"},
    ("routed", "cancelled"): {"manager", "admin"},
    # Admin approval flow (restricted operations)
    ("open", "pending_admin_approval"): {"agent", "manager", "admin"},
    ("pending_admin_approval", "approved"): {"admin"},
    ("pending_admin_approval", "rejected"): {"admin"},
    ("pending_admin_approval", "cancelled"): {"admin"},
    ("pending_admin_approval", "open"): {"admin"},
    ("approved", "assigned"): {"admin", "manager"},
    ("approved", "in_progress"): {"agent", "admin"},
    ("approved", "resolved"): {"agent", "admin"},
    # Rejected tickets
    ("rejected", "closed"): {"manager", "admin"},
    ("rejected", "reopened"): {"manager", "admin"},
    # 2-Month Archival Retention & Renewal Policy
    ("resolved", "archived"): {UserRole.USER.value, UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("closed", "archived"): {UserRole.USER.value, UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("open", "archived"): {UserRole.USER.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("archived", "reopened"): {UserRole.USER.value, UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("archived", "open"): {UserRole.USER.value, UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    # Transitions from reopened
    ("reopened", "in_progress"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("reopened", "assigned"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("reopened", "resolved"): {UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("reopened", "closed"): {UserRole.USER.value, UserRole.AGENT.value, UserRole.MANAGER.value, UserRole.ADMIN.value},
    ("reopened", "cancelled"): {UserRole.MANAGER.value, UserRole.ADMIN.value},
}


def validate_transition(from_status: str, to_status: str, user_roles: List[str]) -> bool:
    if from_status == to_status:
        return True

    from_s = from_status.lower()
    to_s = to_status.lower()

    # Normalize admin role
    roles_lower = {r.lower() for r in user_roles}
    if "admin" in roles_lower:
        # Check if transition itself is logically valid
        valid_targets = [target for (src, target) in ALLOWED_TRANSITIONS.keys() if src == from_s]
        if to_s not in valid_targets:
            raise InvalidStateTransitionError(from_status, to_status, f"Allowed next statuses: {valid_targets}")
        return True

    key = (from_s, to_s)
    if key not in ALLOWED_TRANSITIONS:
        valid_targets = [target for (src, target) in ALLOWED_TRANSITIONS.keys() if src == from_s]
        raise InvalidStateTransitionError(
            from_status, to_status, f"Invalid transition. Valid targets from '{from_s}' are: {valid_targets}"
        )

    allowed_roles = ALLOWED_TRANSITIONS[key]
    if not any(r in allowed_roles for r in roles_lower):
        raise InvalidStateTransitionError(
            from_status,
            to_status,
            f"User with role(s) {list(roles_lower)} is not authorized for this transition. Allowed roles: {list(allowed_roles)}",
        )

    return True


def get_available_transitions(current_status: str, user_roles: List[str]) -> List[str]:
    curr = current_status.lower()
    roles_lower = {r.lower() for r in user_roles}
    is_admin = "admin" in roles_lower

    available = []
    for (src, target), allowed_roles in ALLOWED_TRANSITIONS.items():
        if src == curr:
            if is_admin or any(r in allowed_roles for r in roles_lower):
                available.append(target)
    return available

