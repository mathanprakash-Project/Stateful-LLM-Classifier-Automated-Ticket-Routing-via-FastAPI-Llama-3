"""
Module 4: Workflow Execution Journal — Durable State for LangGraph pipeline.

Records every node's input/output to PostgreSQL, enabling:
- Crash recovery: Resume workflows from the last successful step
- Audit trail: Complete observability of every agent decision
- HITL pausing: Durable pause/resume for human-in-the-loop approvals
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class WorkflowJournalEntry:
    """Represents a single step in the workflow execution journal."""

    def __init__(
        self,
        session_id: str,
        step_name: str,
        step_status: str = "started",
        input_snapshot: Optional[Dict[str, Any]] = None,
        output_snapshot: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
    ):
        self.id = str(uuid4())
        self.session_id = session_id
        self.ticket_id = ticket_id
        self.step_name = step_name
        self.step_status = step_status  # started | completed | failed | paused
        self.input_snapshot = input_snapshot or {}
        self.output_snapshot = output_snapshot or {}
        self.actor_id = actor_id
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "ticket_id": self.ticket_id,
            "step_name": self.step_name,
            "step_status": self.step_status,
            "input_snapshot": self.input_snapshot,
            "output_snapshot": self.output_snapshot,
            "actor_id": self.actor_id,
            "created_at": self.created_at.isoformat(),
        }


class WorkflowJournal:
    """
    In-memory workflow journal that records node execution for observability.

    Production upgrade path:
    - Replace self._entries with PostgreSQL INSERT to workflow_journal table
    - Add SQLAlchemy model with JSONB columns for input/output snapshots
    - Enable crash recovery by reading last successful step on restart

    SQL schema (for future migration):
        CREATE TABLE workflow_journal (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID NOT NULL,
            ticket_id UUID REFERENCES tickets(id),
            step_name VARCHAR(100) NOT NULL,
            step_status VARCHAR(20) NOT NULL,
            input_snapshot JSONB,
            output_snapshot JSONB,
            actor_id UUID,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """

    def __init__(self):
        self._entries: list[WorkflowJournalEntry] = []

    def record_step_start(
        self,
        session_id: str,
        step_name: str,
        input_snapshot: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None,
    ) -> str:
        """Record the start of a workflow step. Returns the entry ID."""
        entry = WorkflowJournalEntry(
            session_id=session_id,
            step_name=step_name,
            step_status="started",
            input_snapshot=_safe_snapshot(input_snapshot),
            actor_id=actor_id,
        )
        self._entries.append(entry)
        logger.debug("Journal: %s started for session %s", step_name, session_id)
        return entry.id

    def record_step_complete(
        self,
        entry_id: str,
        output_snapshot: Optional[Dict[str, Any]] = None,
    ):
        """Record the successful completion of a workflow step."""
        for entry in reversed(self._entries):
            if entry.id == entry_id:
                entry.step_status = "completed"
                entry.output_snapshot = _safe_snapshot(output_snapshot)
                logger.debug("Journal: %s completed", entry.step_name)
                return
        logger.warning("Journal: entry %s not found for completion", entry_id)

    def record_step_failed(self, entry_id: str, error: str):
        """Record a failed workflow step."""
        for entry in reversed(self._entries):
            if entry.id == entry_id:
                entry.step_status = "failed"
                entry.output_snapshot = {"error": error}
                logger.warning("Journal: %s failed — %s", entry.step_name, error)
                return

    def record_step_paused(self, entry_id: str, reason: str = "awaiting_approval"):
        """Record a paused step (HITL approval)."""
        for entry in reversed(self._entries):
            if entry.id == entry_id:
                entry.step_status = "paused"
                entry.output_snapshot = {"pause_reason": reason}
                logger.info("Journal: %s paused — %s", entry.step_name, reason)
                return

    def get_session_journal(self, session_id: str) -> list[Dict[str, Any]]:
        """Get all journal entries for a session."""
        return [
            e.to_dict() for e in self._entries
            if e.session_id == session_id
        ]

    def get_last_successful_step(self, session_id: str) -> Optional[str]:
        """Get the name of the last successfully completed step for crash recovery."""
        completed = [
            e for e in self._entries
            if e.session_id == session_id and e.step_status == "completed"
        ]
        if completed:
            return completed[-1].step_name
        return None

    def get_stats(self) -> Dict[str, int]:
        """Get journal statistics."""
        from collections import Counter
        statuses = Counter(e.step_status for e in self._entries)
        return dict(statuses)


def _safe_snapshot(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a safe snapshot by filtering out large/non-serializable values."""
    if not data:
        return {}
    safe = {}
    for key, value in data.items():
        if key in ("messages",):
            # Don't snapshot full message history — just count
            safe[key] = f"[{len(value)} messages]" if isinstance(value, list) else str(value)[:100]
        elif isinstance(value, (str, int, float, bool, type(None))):
            safe[key] = value
        elif isinstance(value, dict):
            safe[key] = {k: str(v)[:200] for k, v in value.items()}
        elif isinstance(value, list):
            safe[key] = f"[{len(value)} items]"
        else:
            safe[key] = str(value)[:200]
    return safe


# Global journal instance
workflow_journal = WorkflowJournal()
