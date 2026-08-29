"""
Tests for Role-Based Access Control (RBAC) permissions.
"""

import pytest
from app.auth.rbac import has_permission, get_permissions_for_roles
from app.core.constants import PermissionCode, UserRole


def test_user_role_permissions():
    perms = get_permissions_for_roles([UserRole.USER.value])
    assert PermissionCode.TICKET_CREATE.value in perms
    assert PermissionCode.TICKET_READ_OWN.value in perms
    assert PermissionCode.TICKET_READ_ALL.value not in perms
    assert PermissionCode.USER_MANAGE.value not in perms


def test_admin_role_permissions():
    perms = get_permissions_for_roles([UserRole.ADMIN.value])
    assert PermissionCode.TICKET_CREATE.value in perms
    assert PermissionCode.TICKET_READ_ALL.value in perms
    assert PermissionCode.USER_MANAGE.value in perms
    assert PermissionCode.CATEGORY_MANAGE.value in perms


def test_has_permission_helper():
    assert has_permission([UserRole.MANAGER.value], PermissionCode.TICKET_ASSIGN.value) is True
    assert has_permission([UserRole.USER.value], PermissionCode.TICKET_ASSIGN.value) is False

