from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_session
from app.database.models import Analysis, Application
from app.schemas.analysis import StatusUpdate

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("")
def list_applications(session: Session = Depends(get_session)):
    return [
        {
            "id": a.id,
            "analysis_id": a.analysis_id,
            "status": a.status,
            "job_title": j.job_title,
            "company": j.company,
            "updated_at": a.updated_at.isoformat(),
        }
        for a, j in session.execute(select(Application, Analysis).join(Analysis)).all()
    ]


@router.patch("/{application_id}")
def update_application(application_id: str, body: StatusUpdate, session: Session = Depends(get_session)):
    row = session.get(Application, application_id)
    if row is None:
        raise HTTPException(404, "Application not found.")
    row.status = body.status
    session.commit()
    return {"id": row.id, "status": row.status}
