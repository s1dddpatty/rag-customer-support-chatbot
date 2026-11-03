from fastapi import FastAPI
from fastapi import Depends
from fastapi.openapi.utils import get_openapi
# from fastapi import Security

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth
from app.api.document import router as document_router
from app.core.dependencies import get_current_user
from app.core.dependencies import require_role
from contextlib import asynccontextmanager
from app.services.scheduler import start_scheduler, scheduler

# SQLAlchemy models
from app.models.user import User
from app.models.document import Document

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    start_scheduler()
    yield
    # shutdown
    if scheduler.running:
        scheduler.shutdown(wait=False)

app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Database initialization
Base.metadata.create_all(bind=engine)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(document_router)

@app.get("/")
def read_root():
    return {
        "message": f"{settings.app_name} is running"
    }

@app.get("/protected")
def protected_route(user=Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "user": {"user_id": user.user_id, "username": user.username, "user_role": user.user_role}
    }

@app.get("/admin-only")
def admin_route(user=Depends(require_role("admin"))):
    return {
        "message": "Welcome Admin",
        "user": {"user_id": user.user_id, "username": user.username, "user_role": user.user_role}
    }

