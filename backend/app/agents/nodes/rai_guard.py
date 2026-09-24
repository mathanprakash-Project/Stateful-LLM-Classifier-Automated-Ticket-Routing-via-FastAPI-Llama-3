import re
import logging
from typing import Dict, Any, List
# Import AgentState from the existing state definition
try:
    from app.agents.state import AgentState
except ImportError:
    # Fallback if typing is needed without the module
    AgentState = Dict[str, Any]

logger = logging.getLogger(__name__)

PROMISE_PHRASES = [
    "i guarantee", "100% uptime", "will definitely fix", "guaranteed resolution",
    "we promise", "absolutely certain", "zero risk", "no possibility of failure",
    "will never fail", "100% success", "guaranteed fix"
]

LEGAL_PHRASES = [
    "you are entitled to", "we are liable", "legal obligation", "contractual guarantee",
    "sue us", "compensation is due", "damages owed"
]

COMPETITOR_MENTIONS = [
    "servicenow", "zendesk", "jira service", "freshdesk", "salesforce service cloud",
    "bmc remedy", "ivanti"
]

ALLOWED_DOMAINS = [
    "supporthub.com", "supporthub.ai"
]

PII_PATTERNS = {
    # Email
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b": "[REDACTED_EMAIL]",
    # Phone number (simplified 10+ digits)
    r"\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b": "[REDACTED_PHONE]",
    # Credit Card (basic 13-19 digits)
    r"\b(?:\d[ -]*?){13,19}\b": "[REDACTED_CREDIT_CARD]",
    # SSN (XXX-XX-XXXX)
    r"\b\d{3}-\d{2}-\d{4}\b": "[REDACTED_SSN]",
    # IP Address
    r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b": "[REDACTED_IP]"
}

def check_content_safety(text: str) -> List[Dict[str, str]]:
    """Checks for promises, legal phrases, and competitor mentions."""
    issues = []
    text_lower = text.lower()
    
    for phrase in PROMISE_PHRASES:
        if phrase in text_lower:
            issues.append({"type": "promise", "severity": "critical", "detail": f"Found promise phrase: {phrase}"})
            
    for phrase in LEGAL_PHRASES:
        if phrase in text_lower:
            issues.append({"type": "legal", "severity": "critical", "detail": f"Found legal phrase: {phrase}"})
            
    for phrase in COMPETITOR_MENTIONS:
        if phrase in text_lower:
            issues.append({"type": "competitor", "severity": "warning", "detail": f"Found competitor mention: {phrase}"})
            
    return issues

def redact_pii(text: str) -> str:
    """Redacts PII such as email, phone, CC, SSN, and IP."""
    redacted = text
    for pattern, replacement in PII_PATTERNS.items():
        redacted = re.sub(pattern, replacement, redacted)
    return redacted

def check_domain_compliance(text: str) -> List[Dict[str, str]]:
    """Checks for URLs not in the allowed domains."""
    issues = []
    urls = re.findall(r"https?://([-\w.]+)", text)
    for domain in urls:
        is_allowed = any(allowed in domain for allowed in ALLOWED_DOMAINS)
        if not is_allowed:
            issues.append({"type": "unapproved_url", "severity": "warning", "detail": f"Found unapproved domain: {domain}"})
    return issues

def sanitize_response(text: str, issues: List[Dict[str, str]]) -> str:
    """Sanitizes text based on flagged issues."""
    sanitized = text
    for issue in issues:
        if "detail" in issue and ": " in issue["detail"]:
            phrase = issue["detail"].split(": ", 1)[1]
            if issue["type"] == "promise":
                sanitized = re.sub(r'(?i)' + re.escape(phrase), "[POLICY_RESTRICTION: PROMISE_REMOVED]", sanitized)
            elif issue["type"] == "legal":
                sanitized = re.sub(r'(?i)' + re.escape(phrase), "[POLICY_RESTRICTION: LEGAL_REMOVED]", sanitized)
            elif issue["type"] == "competitor":
                sanitized = re.sub(r'(?i)' + re.escape(phrase), "[POLICY_RESTRICTION: COMPETITOR_REMOVED]", sanitized)
    return sanitized

async def rai_guard_node(state: AgentState) -> Dict[str, Any]:
    """
    RAI Guard node for checking and sanitizing response before returning to user.
    """
    response_text = state.get("response_text", "")
    if not response_text:
        return {}
    
    issues = []
    
    # 1. Content safety
    safety_issues = check_content_safety(response_text)
    issues.extend(safety_issues)
    
    # 2. PII protection - always redact
    cleaned_text = redact_pii(response_text)
    
    # 3. Domain compliance
    compliance_issues = check_domain_compliance(cleaned_text)
    issues.extend(compliance_issues)
    
    # If critical issues found, sanitize the response
    if any(issue["severity"] == "critical" for issue in issues):
        cleaned_text = sanitize_response(cleaned_text, issues)
    
    # Log issues for observability
    if issues:
        logger.warning("RAI Guard flagged %d issues: %s", len(issues), [i["type"] for i in issues])

    try:
        from app.core.model_tracker import model_tracker
        pii_count = sum(1 for i in issues if i.get("type") == "pii_redacted")
        safety_count = sum(1 for i in issues if i.get("type") in ["unauthorized_promise", "competitor_mention"])
        model_tracker.record_rai_guard(pii_count=pii_count, safety_flags=safety_count)
    except Exception as e:
        logger.debug("Failed to record RAI telemetry: %s", e)
    
    return {
        "response_text": cleaned_text,
        "rai_flags": issues if issues else None,
    }
