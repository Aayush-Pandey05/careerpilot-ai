# Voice interview coach

From a completed CareerPilot analysis, open **Interview prep** and select **Start voice interview**. GPT-4o mini plans 10–14 main questions based on the resume and target role. It can ask one extra follow-up per question and adapt the next question to the latest answer. The session saves each submitted answer and can be reopened from **Saved sessions**.

- **Read question aloud** uses an installed local browser voice. If none is available, the question remains visible.
- **Record answer** captures microphone audio. Stop recording to transcribe it with local Whisper Base. Review or edit the resulting transcript before selecting **Submit answer**. You can also type directly.
- **Generate interview report** becomes available after all main questions and any remaining follow-up. It uses the transcript and question rubric to produce feedback and practice tasks.

Audio is processed on the computer running FastAPI. Only text goes to OpenAI, including the relevant resume/job context, candidate answers and feedback requests. CareerPilot saves submitted answers and reports in PostgreSQL, and deleting their parent analysis removes its interview sessions. LangSmith uses the project's existing tracing and payload settings.

## Setup

The coach uses the existing `backend/.env` settings `LLM_MODE=live` and `OPENAI_MODEL=gpt-4o-mini`. Install the updated requirements, apply the migration once to your configured database, and restart the backend:

```powershell
cd D:\gen_ai_aat\backend
uv pip install --python ..\.venv\Scripts\python.exe --cache-dir ..\.cache\uv -r requirements.txt
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run the frontend as usual with `npm.cmd run dev` in `D:\gen_ai_aat\frontend`. Use localhost or HTTPS to enable browser microphone access. The first recording downloads the Whisper Base model into `.local/whisper`. To prepare it before an interview, run this in the backend folder:

```powershell
..\.venv\Scripts\python.exe -c "from app.interview.transcription import whisper_model; whisper_model()"
```

For a smoke test, use a synthetic resume and job, record a short answer, check that the transcript can be edited, submit it, then reload and reopen the session. Finish the interview and verify that the report appears alongside the saved transcript.
