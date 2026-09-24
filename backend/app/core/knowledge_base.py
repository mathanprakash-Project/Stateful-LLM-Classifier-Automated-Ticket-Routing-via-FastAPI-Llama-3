import logging
from typing import Dict, Any

from app.core.retrieval import HybridRetriever

# Try to import activity definitions robustly
try:
    from app.core.activity_registry import ACTIVITIES
except ImportError:
    try:
        from app.core.activity_registry import ACTIVITY_REGISTRY as ACTIVITIES
    except ImportError:
        # Fallback empty if registry isn't in expected format
        ACTIVITIES = {}

logger = logging.getLogger(__name__)

def seed_knowledge_base(retriever: HybridRetriever) -> None:
    """Seeds the retriever with initial knowledge base articles."""
    logger.info("Seeding knowledge base...")
    
    # Add activity definitions from registry
    try:
        if isinstance(ACTIVITIES, dict):
            activities_list = ACTIVITIES.items()
        elif isinstance(ACTIVITIES, list):
            activities_list = [(getattr(a, 'id', str(i)), a) for i, a in enumerate(ACTIVITIES)]
        else:
            activities_list = []
            
        for act_id, activity in activities_list:
            name = getattr(activity, "activity_name", getattr(activity, "name", str(act_id)))
            desc = getattr(activity, "description", "")
            
            content = f"Activity: {name} ({act_id})\nDescription: {desc}\n"
            if hasattr(activity, "prerequisites") and activity.prerequisites:
                content += f"Prerequisites: {', '.join(activity.prerequisites)}\n"
            if hasattr(activity, "risk_warning") and activity.risk_warning:
                content += f"Risk Warning: {activity.risk_warning}\n"
            if hasattr(activity, "customer_analogy") and activity.customer_analogy:
                content += f"Analogy: {activity.customer_analogy}\n"
            if hasattr(activity, "customer_summary") and activity.customer_summary:
                content += f"Summary: {activity.customer_summary}\n"
                
            retriever.add_document(
                doc_id=f"activity_{act_id}",
                content=content,
                metadata={"type": "activity_definition", "activity_id": str(act_id)},
                category="definitions"
            )
    except Exception as e:
        logger.error(f"Error seeding activities from registry: {e}")

    # Seed 12 custom knowledge articles covering troubleshooting, resolutions, etc.
    articles = [
        {
            "id": "kb_001",
            "content": "Password Reset Protocol: To reset a user's password, verify their identity using 2FA, then send a secure reset link to their registered email address. Do not provide passwords over the phone.",
            "category": "security",
            "metadata": {"type": "troubleshooting_guide"}
        },
        {
            "id": "kb_002",
            "content": "Server Reboot Procedure: Gracefully shut down active services, notify users if downtime is expected, and issue the reboot command. Monitor the startup logs to ensure all services recover.",
            "category": "infrastructure",
            "metadata": {"type": "resolution_template"}
        },
        {
            "id": "kb_003",
            "content": "Database Migration Guide: Always backup the database before applying schemas. Apply changes during a maintenance window and verify data integrity post-migration.",
            "category": "database",
            "metadata": {"type": "troubleshooting_guide"}
        },
        {
            "id": "kb_004",
            "content": "Network Outage Resolution: Check the physical layer first, then routing tables. If BGP routes are flapping, isolate the offending router and restart the routing daemon.",
            "category": "network",
            "metadata": {"type": "resolution_template"}
        },
        {
            "id": "kb_005",
            "content": "Email Delivery Issues: If emails are bouncing, check the MX records and ensure the sender IP is not on any blacklists. Request delisting if necessary.",
            "category": "communications",
            "metadata": {"type": "troubleshooting_guide"}
        },
        {
            "id": "kb_006",
            "content": "API Rate Limiting: When clients hit the 429 Too Many Requests error, advise them to implement exponential backoff. Do not increase rate limits without approval from the security team.",
            "category": "api",
            "metadata": {"type": "resolution_template"}
        },
        {
            "id": "kb_007",
            "content": "SSL Certificate Renewal: Generate a new CSR, request the certificate from the CA, and deploy it to the load balancers. Verify the chain of trust using external tools.",
            "category": "security",
            "metadata": {"type": "resolution_template"}
        },
        {
            "id": "kb_008",
            "content": "Slow Application Performance: Profile the application endpoints. If database queries are slow, check for missing indexes or n+1 query issues. Implement caching where appropriate.",
            "category": "performance",
            "metadata": {"type": "troubleshooting_guide"}
        },
        {
            "id": "kb_009",
            "content": "VPN Access Denied: Ensure the user's account is active and they belong to the correct AD group. Check if the VPN client is up to date and re-sync the MFA token.",
            "category": "access",
            "metadata": {"type": "troubleshooting_guide"}
        },
        {
            "id": "kb_010",
            "content": "Disk Space Exhaustion: Clear temporary files and rotate large logs. Identify large files using 'du' and archive data older than 90 days to cold storage.",
            "category": "infrastructure",
            "metadata": {"type": "resolution_template"}
        },
        {
            "id": "kb_011",
            "content": "Memory Leak Diagnostics: Monitor JVM heap usage over time. If a leak is suspected, capture a heap dump and analyze it for retained objects. Restart the service as a temporary mitigation.",
            "category": "performance",
            "metadata": {"type": "troubleshooting_guide"}
        },
        {
            "id": "kb_012",
            "content": "Phishing Incident Response: Isolate the affected user's machine, reset their credentials, and run a full antivirus scan. Block the malicious domains on the corporate firewall.",
            "category": "security",
            "metadata": {"type": "resolution_template"}
        }
    ]

    for article in articles:
        retriever.add_document(
            doc_id=article["id"],
            content=article["content"],
            metadata=article["metadata"],
            category=article["category"]
        )

    logger.info("Knowledge base seeded successfully with %d articles.", len(articles))

def add_resolution_to_kb(retriever: HybridRetriever, ticket_data: Dict[str, Any]) -> None:
    """Adds a resolved ticket's resolution to the knowledge base as a flywheel effect."""
    ticket_id = ticket_data.get("id", "unknown")
    resolution = ticket_data.get("resolution", "")
    issue = ticket_data.get("issue_description", "")
    category = ticket_data.get("category", "general")
    
    if not resolution:
        logger.warning(f"No resolution found for ticket {ticket_id}. Not adding to KB.")
        return
        
    content = f"Issue: {issue}\nResolution: {resolution}"
    
    retriever.add_document(
        doc_id=f"ticket_res_{ticket_id}",
        content=content,
        metadata={"type": "resolved_ticket", "ticket_id": ticket_id},
        category=category
    )
    logger.info(f"Added resolution for ticket {ticket_id} to knowledge base.")
