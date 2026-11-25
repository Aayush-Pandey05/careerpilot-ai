from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.database import get_session

router = APIRouter()


@router.get("/health")
def health(session: Session = Depends(get_session)):
    settings = get_settings()
    try:
        session.execute(text("SELECT 1"))
        database = "connected"
    except Exception:
        database = "unavailable"
    return {
        "status": "ok" if database == "connected" else "degraded",
        "database": database,
        "version": "1.0.0",
        "llm_mode": settings.llm_mode,
        "model": settings.openai_model or "Not configured",
        "ai_configured": settings.llm_mode == "mock" or bool(settings.openai_api_key.get_secret_value()),
        "tracing": settings.langsmith_tracing,
        "max_revisions": settings.max_revision_attempts,
        "max_upload_mb": settings.max_upload_mb,
    }
