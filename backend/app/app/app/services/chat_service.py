"""
Chat service managing conversation history, agent execution, draft management, and human approval.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import run_chat_turn
from app.core.exceptions import NotFoundError, ValidationError
from app.models import AITicketDraft, ChatMessage, ChatSession, User
from app.repositories.category_repo import CategoryRepository
from app.repositories.chat_repo import ChatRepository
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import TicketService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.category_repo = CategoryRepository(db)
        self.ticket_service = TicketService(db)

    async def create_session(self, user: User) -> ChatSession:
        return await self.chat_repo.create_session(user.id)

    async def get_session(self, session_id: str, user: User) -> ChatSession:
        session = await self.chat_repo.get_session(session_id)
        if not session or session.user_id != user.id:
            raise NotFoundError("Chat session", session_id)
        return session

    async def list_user_sessions(self, user: User) -> List[ChatSession]:
        return await self.chat_repo.list_user_sessions(user.id)

    async def process_user_message(
        self, session_id: str, user: User, message_text: str, preferred_model: Optional[str] = None
    ) -> Dict[str, Any]:
        session = await self.get_session(session_id, user)

        # 1. Save user message
        await self.chat_repo.add_message(
            session_id=session.id,
            role="user",
            content=message_text,
            message_type="text",
        )

        # 2. Prepare conversation history
        existing_msgs = [
            {"role": m.role, "content": m.content, "type": m.message_type}
            for m in session.messages
        ]

        logger.info("[CHAT_TURN_START] session_id=%s, model=%s, user_msg=%s", session.id, preferred_model, message_text)

        # 3. Run agent turn
        primary_role = user.roles[0].name.lower() if user.roles else "user"
        agent_res = await run_chat_turn(
            session_id=session.id,
            user_id=user.id,
            user_name=user.full_name,
            user_message=message_text,
            existing_messages=existing_msgs,
            current_state=session.agent_state or {},
            user_role=primary_role,
            preferred_model=preferred_model,
        )

        logger.info("[CHAT_TURN_END] agent_res intent=%s, act=%s, missing=%s, draft=%s", agent_res.get("intent"), agent_res.get("activity_code"), agent_res.get("missing_fields"), bool(agent_res.get("draft")))

        response_text = agent_res.get("response_text", "Thank you for the update.")
        draft_data = agent_res.get("draft")
        draft_obj: Optional[AITicketDraft] = None

        # 4. Save generated draft if ready
        if draft_data and agent_res.get("needs_human_approval"):
            # Resolve category name to ID
            cat_name = draft_data.get("category_name", "Software")
            cat_model = await self.category_repo.get_by_name(cat_name)
            if not cat_model:
                all_cats = await self.category_repo.list_all()
                cat_model = all_cats[0] if all_cats else None
            
            if cat_model:
                draft_data["category_id"] = cat_model.id
                draft_data["category_name"] = cat_model.name

                sub_name = draft_data.get("subcategory_name")
                if sub_name:
                    sub_model = await self.category_repo.get_subcategory_by_name(cat_model.id, sub_name)
                    if sub_model:
                        draft_data["subcategory_id"] = sub_model.id

            draft_obj = await self.chat_repo.create_draft(
                session_id=session.id,
                user_id=user.id,
                draft_data=draft_data,
            )
            agent_res["draft_id"] = draft_obj.id

        # 5. Save assistant message
        msg_type = "ticket_draft" if draft_obj else "text"
        await self.chat_repo.add_message(
            session_id=session.id,
            role="assistant",
            content=response_text,
            message_type=msg_type,
            metadata_info={"draft_id": draft_obj.id} if draft_obj else {},
        )

        # 6. Save state back to session
        await self.chat_repo.update_session_state(session.id, agent_res)

        return {
            "response_text": response_text,
            "draft": draft_obj,
            "needs_human_approval": agent_res.get("needs_human_approval", False),
        }

    async def approve_draft(
        self, session_id: str, draft_id: str, user: User, custom_draft_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        session = await self.get_session(session_id, user)
        draft = await self.chat_repo.get_draft(draft_id)

        if not draft or draft.session_id != session.id or draft.user_id != user.id:
            raise NotFoundError("Draft", draft_id)

        if draft.status != "pending_review":
            raise ValidationError(f"Draft is already in status '{draft.status}'.")

        data = dict(draft.draft_data or {})
        if custom_draft_data:
            data.update(custom_draft_data)
            draft.draft_data = data

        # Resolve category ID by name if changed or missing
        cat_id = data.get("category_id")
        cat_name = data.get("category_name")
        all_cats = await self.category_repo.list_all()

        if cat_name and all_cats:
            for c in all_cats:
                if c.name.lower() == cat_name.lower() or cat_name.lower() in c.name.lower():
                    cat_id = c.id
                    break

        if not cat_id:
            if all_cats:
                cat_id = all_cats[0].id
            else:
                raise ValidationError("No valid category found.")

        # Resolve activity code and properties if category changed
        activity_code = data.get("activity_code")
        if cat_name:
            c_low = cat_name.lower()
            if "version" in c_low:
                activity_code = "APPLICATION_VERSION"
                data["execution_mode"] = "Offline"
                data["downtime_required"] = True
                data["requires_admin_approval"] = True
            elif "transfer" in c_low or "client" in c_low:
                activity_code = "CLIENT_DATA_TRANSFER"
                data["execution_mode"] = "Hybrid"
                data["downtime_required"] = False
                data["requires_admin_approval"] = True
            elif "file" in c_low:
                activity_code = "FILE_MANAGEMENT"
                data["execution_mode"] = "Online"
                data["downtime_required"] = False
            elif "ui" in c_low:
                activity_code = "APPLICATION_UI"
                data["execution_mode"] = "Online"
                data["downtime_required"] = False

        ticket_in = TicketCreate(
            title=data.get("title", "Support Request"),
            description=data.get("description", "Created via AI Agent"),
            category_id=cat_id,
            subcategory_id=data.get("subcategory_id"),
            priority=data.get("priority", "medium"),
            meta_info=data.get("meta_info", {}),
            activity_code=activity_code,
            technical_scope=data.get("technical_scope", "application"),
            responsible_team=data.get("responsible_team", "APPLICATION_SUPPORT"),
            requires_admin_approval=data.get("requires_admin_approval", False),
            execution_mode=data.get("execution_mode", "Online"),
            downtime_required=data.get("downtime_required", False),
            downtime_acknowledged=True,
            prerequisites_confirmed=True,
            prerequisites_notes=f"Prerequisites and maintenance schedule confirmed. Window: {data.get('maintenance_window', 'N/A')}",
        )

        ticket = await self.ticket_service.create_ticket(user, ticket_in)

        # Update draft status
        draft.status = "approved"
        draft.ticket_id = ticket.id
        await self.db.commit()

        # Add confirmation message
        confirmation_msg = f"Ticket **{ticket.ticket_number}** has been confirmed and submitted!"
        await self.chat_repo.add_message(
            session_id=session.id,
            role="assistant",
            content=confirmation_msg,
            message_type="ticket_confirmation",
            metadata_info={"ticket_id": ticket.id, "ticket_number": ticket.ticket_number},
        )

        return {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "message": f"Ticket {ticket.ticket_number} created successfully.",
        }

    async def update_draft(
        self, session_id: str, draft_id: str, user: User, updates: Dict[str, Any]
    ) -> AITicketDraft:
        session = await self.get_session(session_id, user)
        draft = await self.chat_repo.get_draft(draft_id)

        if not draft or draft.session_id != session.id or draft.user_id != user.id:
            raise NotFoundError("Draft", draft_id)

        current_data = dict(draft.draft_data)
        for k, v in updates.items():
            if v is not None:
                current_data[k] = v

        updated_draft = await self.chat_repo.update_draft(draft_id, current_data)
        return updated_draft

    async def reject_draft(self, session_id: str, draft_id: str, user: User) -> Dict[str, Any]:
        session = await self.get_session(session_id, user)
        draft = await self.chat_repo.get_draft(draft_id)

        if not draft or draft.session_id != session.id or draft.user_id != user.id:
            raise NotFoundError("Draft", draft_id)

        draft.status = "rejected"
        await self.chat_repo.update_session_state(session.id, {
            "extracted_fields": {},
            "missing_fields": [],
            "draft": None,
            "draft_id": None,
            "needs_human_approval": False,
            "intent": None,
        })
        await self.db.commit()

        await self.chat_repo.add_message(
            session_id=session.id,
            role="assistant",
            content="The ticket draft has been cancelled. What technical issue can I help you resolve?",
            message_type="text",
        )

        return {"message": "Draft rejected."}

