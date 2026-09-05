"""
Centralized Activity Registry for Enterprise Application Support Operations.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ActivityDefinition:
    activity_code: str
    activity_name: str
    description: str
    technical_scope: str  # "application" | "out_of_application_scope" | "non_technical"
    allowed_for_user_request: bool
    restricted_operation: bool
    required_role_for_execution: Optional[str]  # e.g. "admin", "agent"
    responsible_team: str
    requires_admin_approval: bool
    requires_manager_review: bool
    ticket_eligible: bool
    execution_mode: str = "Online"  # "Offline" | "Hybrid" | "Online"
    downtime_required: bool = False
    downtime_description: str = "No Downtime"
    customer_summary: str = ""
    customer_analogy: str = ""
    prerequisites: List[str] = field(default_factory=list)
    risk_warning: str = ""
    approval_workflow: str = "direct_to_agent"  # "admin_to_agent" | "direct_to_agent" | "manager_route"


ACTIVITY_REGISTRY: dict[str, ActivityDefinition] = {
    "APPLICATION_VERSION": ActivityDefinition(
        activity_code="APPLICATION_VERSION",
        activity_name="Application Versioning",
        description="Updating the core runtime engine, background executables, and system binaries to a higher, more stable release.",
        technical_scope="application",
        allowed_for_user_request=True,
        restricted_operation=True,
        required_role_for_execution="admin",
        responsible_team="APPLICATION_SUPPORT",
        requires_admin_approval=True,
        requires_manager_review=False,
        ticket_eligible=True,
        execution_mode="Offline",
        downtime_required=True,
        downtime_description="Yes (Planned Downtime)",
        customer_summary="System executables and engine files are locked while running; all services must be stopped to apply core runtime upgrades.",
        customer_analogy="Think of this as upgrading the engine of a car. Because we are replacing the core moving parts that run the entire software platform, the system must be turned off briefly during the maintenance window so the new files can be safely swapped in.",
        prerequisites=[
            "Target version compatibility check with operating system and database layers.",
            "Verified full backup of the existing global application directory.",
            "Approved maintenance window to halt system services.",
            "Root/admin host permissions to set file execution rights.",
        ],
        risk_warning="Performing version maintenance without compatibility checks or an active backup may lead to prolonged system downtime or executable startup failures.",
        approval_workflow="admin_to_agent",
    ),
    "CLIENT_DATA_TRANSFER": ActivityDefinition(
        activity_code="CLIENT_DATA_TRANSFER",
        activity_name="Client Data Transfer",
        description="Replicating configuration, master records, and operational transactional data from a source environment to a target environment over a network link.",
        technical_scope="application",
        allowed_for_user_request=True,
        restricted_operation=True,
        required_role_for_execution="admin",
        responsible_team="APPLICATION_SUPPORT",
        requires_admin_approval=True,
        requires_manager_review=False,
        ticket_eligible=True,
        execution_mode="Hybrid",
        downtime_required=False,
        downtime_description="No Full Downtime (User Lockout Required)",
        customer_summary="System remains powered on, but active users are locked out from target/source environments to avoid data conflicts.",
        customer_analogy="The system stays powered on, but we temporarily lock out user logins in the target test system. This ensures that while massive amounts of data are being copied over the network, nobody creates partial entries that could corrupt the transfer.",
        prerequisites=[
            "Pre-configured target environment structure.",
            "Active, authorized network communication connection between source and target systems.",
            "Sufficient database disk storage on the target system.",
            "User access temporarily locked on participating environments.",
        ],
        risk_warning="Attempting data transfer without target user lockout or insufficient storage can result in partial data corruption or network transmission timeouts.",
        approval_workflow="admin_to_agent",
    ),
    "FILE_MANAGEMENT": ActivityDefinition(
        activity_code="FILE_MANAGEMENT",
        activity_name="File Management",
        description="Running, scheduling, and monitoring host-level scripts and automated jobs directly from the application platform.",
        technical_scope="application",
        allowed_for_user_request=True,
        restricted_operation=False,
        required_role_for_execution="agent",
        responsible_team="APPLICATION_SUPPORT",
        requires_admin_approval=False,
        requires_manager_review=False,
        ticket_eligible=True,
        execution_mode="Online",
        downtime_required=False,
        downtime_description="No Downtime",
        customer_summary="Background scripts clean, archive, and transfer host files seamlessly while normal business continues.",
        customer_analogy="This is automated background housekeeping. The system runs housekeeping scripts in the background to clean up old interface logs and move files, with zero interruption to everyday user operations.",
        prerequisites=[
            "Authorized administrator credentials to define and trigger external tasks.",
            "Appropriate host-level directory read/write/execute permissions.",
            "Pre-configured and tested command scripts with strict security parameters.",
        ],
        risk_warning="Invalid script paths or insufficient host permissions may cause file processing jobs to fail.",
        approval_workflow="direct_to_agent",
    ),
    "APPLICATION_UI": ActivityDefinition(
        activity_code="APPLICATION_UI",
        activity_name="UI Change and Issues",
        description="Customizing user interfaces, modifying fields, updating brand styling, and diagnosing and fixing frontend runtime/rendering errors.",
        technical_scope="application",
        allowed_for_user_request=True,
        restricted_operation=False,
        required_role_for_execution="agent",
        responsible_team="APPLICATION_SUPPORT",
        requires_admin_approval=False,
        requires_manager_review=False,
        ticket_eligible=True,
        execution_mode="Online",
        downtime_required=False,
        downtime_description="No Downtime",
        customer_summary="Screen adaptations, layout enhancements, and UI error fixes deploy directly with zero business disruption.",
        customer_analogy="We can adjust screen layouts, fix visual bugs, and streamline user entry fields in real time. Once the change or error fix is published, users immediately see the updated interface on their next page load without any system restart.",
        prerequisites=[
            "Administrator authorizations for interface customizing tools and designers.",
            "Active backend data services (APIs/gateways) connecting UI elements to business logic.",
            "Tracked deployment package to promote changes from development to production.",
        ],
        risk_warning="Deploying unverified UI custom scripts may cause layout distortion on mobile or older browser viewports.",
        approval_workflow="direct_to_agent",
    ),

    "SERVER": ActivityDefinition(
        activity_code="SERVER",
        activity_name="Server / Infrastructure",
        description="Server down, CPU/memory issues, restart required, deployment issues",
        technical_scope="out_of_application_scope",
        allowed_for_user_request=True,
        restricted_operation=False,
        required_role_for_execution=None,
        responsible_team="INFRASTRUCTURE",
        requires_admin_approval=False,
        requires_manager_review=True,
        ticket_eligible=True,
        execution_mode="Offline",
        downtime_required=True,
        downtime_description="Potential Downtime (Server level)",
        customer_summary="Handled by Infrastructure Systems Engineering team upon Manager Review.",
        customer_analogy="Core operating system and server hardware maintenance managed outside application support.",
        prerequisites=[],
        risk_warning="Server level modifications affect all hosted services.",
        approval_workflow="manager_route",
    ),
    "DATABASE": ActivityDefinition(
        activity_code="DATABASE",
        activity_name="Database",
        description="Database connection failures, storage full, performance issues, data corruption",
        technical_scope="out_of_application_scope",
        allowed_for_user_request=True,
        restricted_operation=False,
        required_role_for_execution=None,
        responsible_team="DATABASE",
        requires_admin_approval=False,
        requires_manager_review=True,
        ticket_eligible=True,
        execution_mode="Offline",
        downtime_required=True,
        downtime_description="Potential Downtime (DB level)",
        customer_summary="Handled by Database Administrator (DBA) team upon Manager Review.",
        customer_analogy="Database engine and storage tuning managed directly by dedicated DBAs.",
        prerequisites=[],
        risk_warning="Database table locking can pause active application queries.",
        approval_workflow="manager_route",
    ),
    "NETWORK": ActivityDefinition(
        activity_code="NETWORK",
        activity_name="Network",
        description="Connectivity issues, firewall/DNS, VPN problems, bandwidth",
        technical_scope="out_of_application_scope",
        allowed_for_user_request=True,
        restricted_operation=False,
        required_role_for_execution=None,
        responsible_team="NETWORK",
        requires_admin_approval=False,
        requires_manager_review=True,
        ticket_eligible=True,
        execution_mode="Online",
        downtime_required=False,
        downtime_description="No Planned Downtime",
        customer_summary="Handled by Corporate Network and Firewall Security team.",
        customer_analogy="Network routing, VPN tunnels, and gateway configurations.",
        prerequisites=[],
        risk_warning="Firewall rule modifications must follow infosec protocols.",
        approval_workflow="manager_route",
    ),
    "SECURITY": ActivityDefinition(
        activity_code="SECURITY",
        activity_name="Security",
        description="Access violations, vulnerability reports, compliance, security audit",
        technical_scope="out_of_application_scope",
        allowed_for_user_request=True,
        restricted_operation=False,
        required_role_for_execution=None,
        responsible_team="SECURITY",
        requires_admin_approval=False,
        requires_manager_review=True,
        ticket_eligible=True,
        execution_mode="Online",
        downtime_required=False,
        downtime_description="No Downtime",
        customer_summary="Handled by Enterprise Infosec & Compliance Team.",
        customer_analogy="Information security reviews and vulnerability remediations.",
        prerequisites=[],
        risk_warning="Security incidents require high confidentiality.",
        approval_workflow="manager_route",
    ),
    "OTHER_TECHNICAL": ActivityDefinition(
        activity_code="OTHER_TECHNICAL",
        activity_name="Other Technical",
        description="Integration issues, API issues, third-party system problems",
        technical_scope="out_of_application_scope",
        allowed_for_user_request=True,
        restricted_operation=False,
        required_role_for_execution=None,
        responsible_team="APPLICATION_SUPPORT",
        requires_admin_approval=False,
        requires_manager_review=True,
        ticket_eligible=True,
        execution_mode="Online",
        downtime_required=False,
        downtime_description="No Downtime",
        customer_summary="Custom integrations and external third-party API issues.",
        customer_analogy="Third-party vendor communication and API integrations.",
        prerequisites=[],
        risk_warning="External API changes must adhere to vendor rate limits.",
        approval_workflow="manager_route",
    ),
    "NON_TECHNICAL": ActivityDefinition(
        activity_code="NON_TECHNICAL",
        activity_name="Non-Technical",
        description="Personal requests, HR, leave, salary, non-work topics",
        technical_scope="non_technical",
        allowed_for_user_request=False,
        restricted_operation=False,
        required_role_for_execution=None,
        responsible_team="NONE",
        requires_admin_approval=False,
        requires_manager_review=False,
        ticket_eligible=False,
        execution_mode="Online",
        downtime_required=False,
        downtime_description="Not Applicable",
        customer_summary="Non-technical questions outside IT operations.",
        customer_analogy="Inquiries regarding HR, payroll, or facilities.",
        prerequisites=[],
        risk_warning="No technical tickets can be created for non-work queries.",
        approval_workflow="direct_to_agent",
    ),
    "UNKNOWN": ActivityDefinition(
        activity_code="UNKNOWN",
        activity_name="Unknown",
        description="Cannot determine the nature of the request",
        technical_scope="application",
        allowed_for_user_request=True,
        restricted_operation=False,
        required_role_for_execution=None,
        responsible_team="APPLICATION_SUPPORT",
        requires_admin_approval=False,
        requires_manager_review=False,
        ticket_eligible=True,
        execution_mode="Online",
        downtime_required=False,
        downtime_description="No Downtime",
        customer_summary="General unclassified inquiry.",
        customer_analogy="General questions pending diagnostic clarification.",
        prerequisites=[],
        risk_warning="None.",
        approval_workflow="direct_to_agent",
    ),
}


def get_activity(activity_code: str) -> ActivityDefinition:
    """Look up an activity definition by code. Returns UNKNOWN if not found."""
    return ACTIVITY_REGISTRY.get(activity_code, ACTIVITY_REGISTRY["UNKNOWN"])


def get_all_activities() -> list[ActivityDefinition]:
    """Return all registered activity definitions."""
    return list(ACTIVITY_REGISTRY.values())


def get_ticket_eligible_activities() -> list[ActivityDefinition]:
    """Return only activities that can result in ticket creation."""
    return [a for a in ACTIVITY_REGISTRY.values() if a.ticket_eligible]


SUPPORT_TEAM_ACTIVITIES_OVERVIEW_RESPONSE = (
    "👋 Hello! We're your Enterprise Application Support AI Team.\n\n"
    "We are here to assist you with our 4 supported technical application activities:\n\n"
    "🖥️ Application UI Maintenance (Online · No Downtime) — Interface adaptations, layout adjustments, and screen error fixes.\n"
    "📁 File Management Operations (Online · No Downtime) — Scheduled archiving scripts, storage cleanup, and file synchronization.\n"
    "🔄 Client Data Transfer (Hybrid · User Lockout) — Tenant data synchronization and client-to-client migration.\n"
    "⚙️ Application Version Maintenance (Offline · Planned Downtime) — Core runtime version upgrades, binary deployments, and patches.\n\n"
    "💬 Please describe your specific maintenance request or technical issue, and our team will guide you through prerequisites, downtime verification, and ticket drafting!"
)


def is_greeting_or_activity_overview(text: str) -> bool:
    """
    Returns True if the user's message is a greeting or an inquiry asking for an overview of supported activities,
    capabilities, scope, or what the support team does.
    """
    import re
    q = (text or "").lower().strip()
    if not q:
        return False

    cleaned = re.sub(r"[^\w\s]", "", q).strip()

    # Exact standalone greetings
    greetings = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings", "help", "who are you"}
    if cleaned in greetings:
        return True

    # Greeting prefixes like "hello team", "hi assistant"
    if any(cleaned.startswith(g + " ") for g in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        action_keywords = ["upgrade", "downgrade", "version", "patch", "transfer", "client", "file", "ui", "broken", "issue", "bug", "error", "fail", "slow", "tkt-"]
        if not any(w in cleaned for w in action_keywords):
            return True

    # Check for queries about activities / capabilities / scope / what we do
    activity_inquiry_patterns = [
        r"\bactivit(y|ies)\b",
        r"\bcapabilit(y|ies)\b",
        r"\bservices?\b",
        r"\bwhat (can|do) you do\b",
        r"\bwhat do you support\b",
        r"\bunder your scope\b",
        r"\bhow can you help\b",
        r"\bshort descr[i|p]ption\b",
        r"\b(list|overview|summary|description) of (the )?activities\b",
    ]
    if any(re.search(pat, cleaned) for pat in activity_inquiry_patterns):
        # Exclude active ticket actions (e.g. "I want to start a client data transfer" or "upgrade application version")
        active_request_phrases = [
            "start", "run", "execute", "create ticket", "open ticket", "raise ticket",
            "upgrade to", "downgrade to", "patch to", "transfer from client", "upload file",
            "download file", "button broken", "screen not loading", "error in", "failed to"
        ]
        if any(p in cleaned for p in active_request_phrases):
            return False
        return True

    return False


def check_prereq_ack(text: str) -> bool:
    """Check if the user confirmed that prerequisites are done/completed/verified."""
    import re
    lower = (text or "").lower()
    # If explicitly stated as not done or pending
    if re.search(r"\b(not yet|not done|pending|incomplete|haven't|havent|in progress|not completed|not verified)\b", lower):
        return False
    # If user is asking a question about prerequisites
    if re.search(r"\b(what are|explain|show|list)\s+prereq", lower):
        return False
    prereq_patterns = [
        r"\bprereq(uisite)?s?\s*(done|completed|verified|checked|ok|ready|all done)\b",
        r"\b(prereq|prerequisites|prerequisite)\b.*\b(done|yes|ok|completed|verified|ready)\b",
        r"\b(yes|done|completed|verified|ready|prepared|all done|all set|confirmed)\b",
    ]
    return any(re.search(pat, lower) for pat in prereq_patterns)


def is_prereq_explicitly_pending(text: str) -> bool:
    """Check if the user explicitly stated that prerequisites are NOT yet done or are pending."""
    import re
    lower = (text or "").lower()
    return bool(re.search(r"\b(not yet|not done|pending|incomplete|haven't|havent|in progress|not completed|not verified)\b", lower))


def check_downtime_window(text: str) -> bool:
    """Check if the user specified a maintenance window or downtime schedule."""
    import re
    lower = (text or "").lower()
    time_patterns = [
        r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b",
        r"\b\d{1,2}:\d{2}\s*(to|-)\s*\d{1,2}:\d{2}\b",
        r"\b\d{1,2}:\d{2}\b",
        r"\b(utc|gmt|est|pst|ist|cst)\b",
        r"\b(saturday|sunday|monday|tuesday|wednesday|thursday|friday|weekend)\b",
        r"\b(midnight|tonight|tomorrow)\b",
        r"\b\d{1,2}\s*(hours?|hrs?)\b",
        r"\b(maintenance window|downtime window|window is|scheduled for|scheduled at|between \d|from \d)\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    ]
    return any(re.search(pat, lower) for pat in time_patterns)



