"""
Custom exception hierarchy for AI-Powered Ticket Management System.
"""

from typing import Any, Optional


class AppBaseException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(AppBaseException):
    def __init__(self, message: str = "Invalid credentials", details: Optional[dict[str, Any]] = None):
        super().__init__(message=message, code="INVALID_CREDENTIALS", status_code=401, details=details)


class AuthorizationError(AppBaseException):
    def __init__(self, message: str = "Permission denied", details: Optional[dict[str, Any]] = None):
        super().__init__(message=message, code="FORBIDDEN", status_code=403, details=details)


class NotFoundError(AppBaseException):
    def __init__(self, resource: str, resource_id: Any = None):
        msg = f"{resource} not found" if not resource_id else f"{resource} '{resource_id}' not found"
        super().__init__(message=msg, code="RESOURCE_NOT_FOUND", status_code=404)


class ValidationError(AppBaseException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class InvalidStateTransitionError(AppBaseException):
    def __init__(self, from_state: str, to_state: str, reason: Optional[str] = None):
        msg = f"Cannot transition ticket from '{from_state}' to '{to_state}'"
        if reason:
            msg += f": {reason}"
        super().__init__(message=msg, code="INVALID_STATUS_TRANSITION", status_code=422)


class ConcurrencyConflictError(AppBaseException):
    def __init__(self, message: str = "Ticket has been modified by another user. Please refresh."):
        super().__init__(message=message, code="CONCURRENCY_CONFLICT", status_code=409)


class DuplicateResourceError(AppBaseException):
    def __init__(self, message: str = "Duplicate resource"):
        super().__init__(message=message, code="DUPLICATE_RESOURCE", status_code=409)

