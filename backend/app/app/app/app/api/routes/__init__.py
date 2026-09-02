from app.api.routes.auth import router as auth_router
from app.api.routes.tickets import router as ticket_router
from app.api.routes.chat import router as chat_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.categories import router as category_router
from app.api.routes.users import router as user_router
from app.api.routes.events import router as event_router

__all__ = [
    "auth_router",
    "ticket_router",
    "chat_router",
    "dashboard_router",
    "category_router",
    "user_router",
    "event_router",
]

