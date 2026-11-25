# Windows setup and deployment

Run commands in VS Code PowerShell. Replace the root path only if you move the project. Keep API keys in environment files, never in chat or source.

## Already prepared in this workspace

The dependencies and local environment files have been created. A portable PostgreSQL server is installed under `.local/postgres`, with its data under `.local/pgdata`. It uses loopback port **55432**, and backend/.env already points to it. This local instance avoids the Docker Desktop startup failure on this computer. Docker is not needed for this prepared setup.

To start or reopen the demo:

```powershell
cd D:\gen_ai_aat
.\start.ps1
```

Open http://localhost:3000 after the frontend is ready. The script starts the local database if necessary, applies migrations and starts hidden backend/frontend processes. Logs are in `.local`. After adding keys or changing backend settings, use `.\start.ps1 -Restart` to restart the backend process owned by the launcher. You can also use the separate-terminal commands below on a fresh installation.

If the system `python` command is the Windows Store stub, the prepared `.venv\Scripts\python.exe` works directly. The bundled interpreter used to create it is `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

## 1 Install prerequisites

Install Python 3.11+, Node.js 20.9+ and PostgreSQL, or Docker Desktop for the database. Confirm `python --version`, `node --version` and `npm.cmd --version`. A Windows Store Python alias is not a working Python install. If `Activate.ps1` is blocked, call `.venv\Scripts\python.exe` directly; changing machine execution policy is unnecessary.

## 2 Install the project

```powershell
cd D:\gen_ai_aat
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local
npm.cmd install --prefix frontend
```

Do not overwrite your environment files if they already contain your credentials. Dependencies resolved during verification are recorded in `backend/requirements.lock.txt` and `frontend/package-lock.json`; use `pip install -r backend/requirements.lock.txt` and `npm.cmd ci --prefix frontend` for repeatable installation.

## 3 Start PostgreSQL

Option A, Docker Desktop running:

```powershell
cd D:\gen_ai_aat
docker compose up -d postgres
docker compose ps
```

The example backend URL matches the local Docker user/password/database. It binds PostgreSQL to loopback. `docker compose stop` stops it while preserving data. Avoid deleting the volume if you want to preserve history.

Option B, native PostgreSQL: use the [official Windows downloads](https://www.postgresql.org/download/windows/) and pgAdmin or SQL Shell. Connect as your database administrator and run:

```sql
CREATE USER careerpilot WITH PASSWORD 'choose_a_local_password';
CREATE DATABASE careerpilot OWNER careerpilot;
```

Set `DATABASE_URL=postgresql+psycopg://careerpilot:YOUR_PASSWORD@localhost:5432/careerpilot` in backend/.env. URL-encode special characters in the password. Do not include the placeholder literally. PostgreSQL is the only supported database; there is no SQLite fallback.

## 4 Migrate and launch the backend

```powershell
cd D:\gen_ai_aat\backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://localhost:8000/api/v1/health. `database` must be `connected`. The API can start without a reachable database but reports degraded health; saving/history require PostgreSQL and migrated tables.

## 5 Launch the frontend

New terminal:

```powershell
cd D:\gen_ai_aat\frontend
npm.cmd run dev
```

Open http://localhost:3000. The frontend environment file should contain `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`. Only this public API URL belongs in the browser. A frontend restart is needed after environment changes; production builds embed this value.

## 6 Run the offline demonstration

Open New analysis, download the synthetic PDF or DOCX, upload it, choose Use sample role and run. Actual events appear even though offline processing is fast. The results page preserves the timeline. Offline extraction expects readable section headings and a limited skill vocabulary; use live mode for more flexible language understanding.

## 7 Configure OpenAI manually

Create a key in the [OpenAI API platform](https://platform.openai.com/api-keys), with API project access and billing as required by your account. API usage is separately billed from ChatGPT subscriptions. In `backend/.env` set:

```env
OPENAI_API_KEY=your_private_key_here
OPENAI_MODEL=an_api_model_available_to_your_project
LLM_MODE=live
```

No model is silently selected. Choose an API model supporting structured outputs from the [model catalog](https://developers.openai.com/api/docs/models). Restart FastAPI and run the synthetic analysis. Check System & settings for live mode and configured model. A successful live result and actual LLM call traces verify the connection, rather than a configuration flag alone. Do not print the key to verify it.

Missing key/model prevents startup. Authentication errors require checking the key/project; model-not-found requires a model your project can access; quota/billing errors require API billing or limits; rate limits require lower request volume; timeouts may need shorter documents or a higher bounded timeout. Use LangSmith or backend diagnostics without sharing credentials. Do not repeatedly retry quota/authentication failures.

## 8 Configure LangSmith

Follow `docs/LANGSMITH.md`. LangSmith and OpenAI keys are separate. Tracing may run in mock mode too, but mock traces do not contain real OpenAI model calls.

## Optional production launch

Build the frontend with `npm.cmd run build`, then `npm.cmd start`. Run Uvicorn without `--reload`. Use managed PostgreSQL, a private application database user, HTTPS and managed secrets. Apply migrations before traffic. Add login, authorization, retention policies, backup/restore tests, upload and API rate limits, proxy request size limits and monitoring. Long-lived SSE workflows currently stop on disconnect/server restart; add durable workers/checkpointing if that behavior is needed. Do not expose the unauthenticated local API publicly.
