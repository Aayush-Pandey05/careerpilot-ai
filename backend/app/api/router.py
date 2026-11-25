from fastapi import APIRouter

from app.api.routes import analyses, applications, health
from app.interview.routes import router as interview_router

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(analyses.router)
router.include_router(applications.router)
router.include_router(interview_router)
