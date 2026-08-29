"""
Role-Based Access Control definitions and permission helpers.
"""

from typing import Set
from app.core.constants import PermissionCode, UserRole

# Standard role-to-permission mapping
ROLE_PERMISSIONS: dict[UserRole, Set[PermissionCode]] = {
    UserRole.USER: {
        PermissionCode.TICKET_CREATE,
        PermissionCode.TICKET_READ_OWN,
        PermissionCode.TICKET_UPDATE_OWN,
        PermissionCode.TICKET_CLOSE_OWN,
        PermissionCode.TICKET_REOPEN,
        PermissionCode.CHAT_CREATE,
        PermissionCode.CHAT_READ_OWN,
    },
    UserRole.AGENT: {
        PermissionCode.TICKET_CREATE,
        PermissionCode.TICKET_READ_OWN,
        PermissionCode.TICKET_READ_ASSIGNED,
        PermissionCode.TICKET_UPDATE_ASSIGNED,
        PermissionCode.TICKET_ASSIGN,
        PermissionCode.TICKET_ESCALATE,
        PermissionCode.CHAT_CREATE,
        PermissionCode.CHAT_READ_OWN,
    },
    UserRole.MANAGER: {
        PermissionCode.TICKET_CREATE,
        PermissionCode.TICKET_READ_OWN,
        PermissionCode.TICKET_READ_ASSIGNED,
        PermissionCode.TICKET_READ_TEAM,
        PermissionCode.TICKET_UPDATE_ASSIGNED,
        PermissionCode.TICKET_UPDATE_ALL,
        PermissionCode.TICKET_ASSIGN,
        PermissionCode.TICKET_ESCALATE,
        PermissionCode.TICKET_REOPEN,
        PermissionCode.DASHBOARD_ANALYTICS,
    },
    UserRole.ADMIN: {
        PermissionCode.TICKET_CREATE,
        PermissionCode.TICKET_READ_OWN,
        PermissionCode.TICKET_READ_ASSIGNED,
        PermissionCode.TICKET_READ_TEAM,
        PermissionCode.TICKET_READ_ALL,
        PermissionCode.TICKET_UPDATE_OWN,
        PermissionCode.TICKET_UPDATE_ASSIGNED,
        PermissionCode.TICKET_UPDATE_ALL,
        PermissionCode.TICKET_ASSIGN,
        PermissionCode.TICKET_ESCALATE,
        PermissionCode.TICKET_CLOSE_OWN,
        PermissionCode.TICKET_REOPEN,
        PermissionCode.CHAT_CREATE,
        PermissionCode.CHAT_READ_OWN,
        PermissionCode.USER_MANAGE,
        PermissionCode.CATEGORY_MANAGE,
        PermissionCode.AUDIT_READ,
        PermissionCode.DASHBOARD_ANALYTICS,
    },
}


def get_permissions_for_roles(roles: list[str]) -> set[str]:
    permissions: set[str] = set()
    for role_name in roles:
        try:
            role_enum = UserRole(role_name.lower())
            perms = ROLE_PERMISSIONS.get(role_enum, set())
            permissions.update(p.value for p in perms)
        except ValueError:
            continue
    return permissions


def has_permission(user_roles: list[str], required_permission: str) -> bool:
    user_perms = get_permissions_for_roles(user_roles)
    return required_permission in user_perms

