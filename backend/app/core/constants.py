"""
Enums and application constants for AI-Powered Ticket Management System.
"""

from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    MANAGER = "manager"
    ADMIN = "admin"


class TicketStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    CANCELLED = "cancelled"
    PENDING_MANAGER_ROUTING = "pending_manager_routing"
    PENDING_ADMIN_APPROVAL = "pending_admin_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROUTED = "routed"


class ActivityCode(str, Enum):
    APPLICATION_UI = "APPLICATION_UI"
    APPLICATION_VERSION = "APPLICATION_VERSION"
    CLIENT_DATA_TRANSFER = "CLIENT_DATA_TRANSFER"
    FILE_MANAGEMENT = "FILE_MANAGEMENT"
    APPLICATION_OTHER = "APPLICATION_OTHER"
    SERVER = "SERVER"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    SECURITY = "SECURITY"
    OTHER_TECHNICAL = "OTHER_TECHNICAL"
    NON_TECHNICAL = "NON_TECHNICAL"
    UNKNOWN = "UNKNOWN"


class OperationStatus(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_EXECUTION = "in_execution"
    COMPLETED = "completed"
    FAILED = "failed"


class TechnicalScope(str, Enum):
    APPLICATION = "application"
    OUT_OF_APPLICATION_SCOPE = "out_of_application_scope"
    NON_TECHNICAL = "non_technical"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DraftStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ChatSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChatMessageType(str, Enum):
    TEXT = "text"
    TICKET_DRAFT = "ticket_draft"
    TICKET_CONFIRMATION = "ticket_confirmation"
    SYSTEM = "system"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class PermissionCode(str, Enum):
    TICKET_CREATE = "ticket:create"
    TICKET_READ_OWN = "ticket:read_own"
    TICKET_READ_ASSIGNED = "ticket:read_assigned"
    TICKET_READ_TEAM = "ticket:read_team"
    TICKET_READ_ALL = "ticket:read_all"
    TICKET_UPDATE_OWN = "ticket:update_own"
    TICKET_UPDATE_ASSIGNED = "ticket:update_assigned"
    TICKET_UPDATE_ALL = "ticket:update_all"
    TICKET_ASSIGN = "ticket:assign"
    TICKET_ESCALATE = "ticket:escalate"
    TICKET_CLOSE_OWN = "ticket:close_own"
    TICKET_REOPEN = "ticket:reopen"
    TICKET_DELETE = "ticket:delete"
    CHAT_CREATE = "chat:create"
    CHAT_READ_OWN = "chat:read_own"
    USER_MANAGE = "user:manage"
    CATEGORY_MANAGE = "category:manage"
    AUDIT_READ = "audit:read"
    DASHBOARD_ANALYTICS = "dashboard:analytics"

