from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.database.database import get_session
from app.database.models import Analysis
from app.interview.coach import adapt_interview, evaluate_interview, interview_context, plan_interview
from app.interview.models import InterviewSession
from app.interview.schemas import Answer
from app.interview.transcription import MAX_AUDIO_BYTES, AudioError, transcribe

router = APIRouter(prefix="/interviews", tags=["Interviews"])


def session_view(interview: InterviewSession) -> dict:
    turns = interview.turns
    answered = sum(not turn["follow_up"] for turn in turns)
    question = None
    if turns and turns[-1].get("next_follow_up"):
        question = {"number": answered, "text": turns[-1]["next_follow_up"], "follow_up": True}
    elif answered < len(interview.plan):
        question = {
            "number": answered + 1,
            "text": interview.plan[answered]["question"],
            "follow_up": False,
        }
    return {
        "id": interview.id,
        "version": interview.version,
        "total": len(interview.plan),
        "answered": answered,
        "question": question,
        "turns": [
            {key: turn[key] for key in ("number", "question", "answer", "follow_up")} for turn in turns
        ],
        "report": interview.report,
    }


def get_interview(db: Session, interview_id: str) -> InterviewSession:
    interview = db.get(InterviewSession, interview_id)
    if interview is None:
        raise HTTPException(404, "Interview session not found.")
    return interview


def save(db: Session):
    try:
        db.commit()
    except StaleDataError as exc:
        db.rollback()
        raise HTTPException(409, "This interview changed. Reopen it to continue.") from exc


def require_live_model():
    settings = get_settings()
    if settings.llm_mode != "live" or settings.openai_model != "gpt-4o-mini":
        raise HTTPException(503, "Set LLM_MODE=live and OPENAI_MODEL=gpt-4o-mini for the interview coach.")


@router.get("/analysis/{analysis_id}")
def list_interviews(analysis_id: str, db: Session = Depends(get_session)):
    rows = db.scalars(
        select(InterviewSession)
        .where(InterviewSession.analysis_id == analysis_id)
        .order_by(InterviewSession.created_at.desc())
    )
    return [{"id": row.id, "created_at": row.created_at, "completed": row.report is not None} for row in rows]


@router.post("/analysis/{analysis_id}", status_code=201)
async def start_interview(analysis_id: str, db: Session = Depends(get_session)):
    require_live_model()
    analysis = db.get(Analysis, analysis_id)
    if analysis is None or analysis.result is None:
        raise HTTPException(404, "Saved analysis not found.")
    payload = analysis.result.payload
    if not payload.get("resume") or not payload.get("job"):
        raise HTTPException(409, "Finish the resume and job analysis first.")
    context = interview_context(analysis)
    db.rollback()
    try:
        plan = await plan_interview(context)
    except Exception as exc:
        raise HTTPException(
            502, "Could not generate interview questions. Check model access and retry."
        ) from exc
    interview = InterviewSession(analysis_id=analysis_id, plan=plan, turns=[])
    db.add(interview)
    save(db)
    return session_view(interview)


@router.get("/{interview_id}")
def read_interview(interview_id: str, db: Session = Depends(get_session)):
    return session_view(get_interview(db, interview_id))


@router.post("/{interview_id}/transcription")
async def transcribe_answer(
    interview_id: str, audio: UploadFile = File(...), db: Session = Depends(get_session)
):
    if session_view(get_interview(db, interview_id))["question"] is None:
        raise HTTPException(409, "This interview has no pending question.")
    db.rollback()
    try:
        data = await audio.read(MAX_AUDIO_BYTES + 1)
    finally:
        await audio.close()
    try:
        return {"text": await run_in_threadpool(transcribe, data)}
    except AudioError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            503,
            "Local Whisper is unavailable. Check the backend dependencies and model download, or type your answer.",
        ) from exc


@router.post("/{interview_id}/answers")
async def submit_answer(interview_id: str, answer: Answer, db: Session = Depends(get_session)):
    require_live_model()
    interview = get_interview(db, interview_id)
    question = session_view(interview)["question"]
    if question is None or answer.version != interview.version:
        raise HTTPException(409, "This question is no longer current. Reopen the interview to continue.")
    turn = {
        "number": question["number"],
        "question": question["text"],
        "follow_up": question["follow_up"],
        "answer": answer.text,
    }
    # Release the read connection during the model request. The original version still
    # participates in the optimistic update when the detached row is attached again.
    db.expunge(interview)
    db.rollback()
    try:
        decision = await adapt_interview(interview.plan, interview.turns, turn)
    except Exception as exc:
        raise HTTPException(
            502, "Could not choose the next question. Your draft can be submitted again."
        ) from exc
    if not turn["follow_up"] and decision.follow_up:
        turn["next_follow_up"] = decision.follow_up
    elif turn["number"] < len(interview.plan) and decision.next_question:
        next_index = turn["number"]
        if decision.next_question.casefold() not in {
            text.casefold() for text in [q["question"] for q in interview.plan] + [turn["question"]]
        }:
            plan = list(interview.plan)
            plan[next_index] = {**plan[next_index], "question": decision.next_question}
            interview.plan = plan
    interview.turns = [*interview.turns, turn]
    db.add(interview)
    save(db)
    return session_view(interview)


@router.post("/{interview_id}/report")
async def create_report(interview_id: str, db: Session = Depends(get_session)):
    interview = get_interview(db, interview_id)
    if interview.report is not None:
        return session_view(interview)
    require_live_model()
    if session_view(interview)["question"] is not None:
        raise HTTPException(409, "Complete all main questions and any pending follow-up first.")
    db.expunge(interview)
    db.rollback()
    try:
        interview.report = await evaluate_interview(interview.plan, interview.turns)
    except Exception as exc:
        raise HTTPException(
            502, "Could not generate feedback. Your answers are saved. Retry the report."
        ) from exc
    db.add(interview)
    save(db)
    return session_view(interview)
