# Verification and handoff

## Live deployment verified on 25 November 2026

The public application is available at https://careerpilot-ai-aat.vercel.app. Its frontend runs on Vercel Hobby, its HTTPS backend runs on AWS EC2, and its database runs on Neon PostgreSQL.

- The production frontend build passed after updating Next.js to 16.4.5. npm reported zero known vulnerabilities after the update.
- The backend Linux container built successfully, including the local Whisper base model. Its test run passed 54 tests, with two database integration tests skipped because TEST_DATABASE_URL was not supplied to that run.
- Eleven live deployment checks passed using synthetic inputs. They covered HTTPS and database health, the public frontend, production CORS, invalid-upload handling, all five analysis agents and SSE progress, saved analysis/history, PDF export, application status updates, interview planning, Whisper transcription, and a completed interview report.
- The live interview test completed 14 main questions and two follow-ups. Its feedback report was saved, reopened through the API, and displayed in the public frontend.
- Physical microphone capture and speaker playback were not verified in that deployment test. Speech transcription was verified using a synthetic recorded answer.

The dated sections below record earlier local verification and configuration.

Verified on 30 October 2026 in this Windows workspace.

## Actual results

- Full Pytest suite with real PostgreSQL enabled: **49 passed in 6.42 seconds**, no skips or failures.
- Backend line coverage: **90%**, 801 statements, 81 not executed. External live-model calls are among the unexecuted paths.
- Ten local synthetic evaluation cases: all eight code checks passed for every case. These are a small regression set, not a general quality benchmark.
- Ruff checks: passed for app, tests and scripts.
- Frontend TypeScript check: passed.
- Next.js production build: passed using Webpack. Generated dashboard, analyze, history, settings and dynamic results pages.
- Alembic initial migration applied successfully to PostgreSQL.
- Real browser flow verified: synthetic PDF upload, POST SSE analysis, saved result, source evidence, review outcome, editable application, save and review, report download and history/dashboard updates. A second real HTTP POST with the DOCX fixture returned 201 and persisted a different role. The downloaded report had two readable PDF pages.
- Responsive interface inspected at desktop and 390-pixel mobile width; a visually hidden table label causing horizontal overflow was corrected.
- Presentation guide: 18 PDF pages rendered and visually inspected, including every page.

No OpenAI API key or LangSmith API key was supplied. **Live OpenAI requests, cloud LangSmith tracing and cloud evaluation experiments were not executed.** Implementations and exact configuration instructions are included; these remain manual external checks.

## Prepared local environment

- Project root: `D:\gen_ai_aat`.
- Python 3.12.14 virtual environment in `.venv` with backend dependencies installed.
- Next.js 16.4.3, React 19 and Tailwind 4 dependencies installed under frontend/node_modules.
- PostgreSQL 17.11 portable vendor binaries under `.local/postgres/pgsql`.
- Database data under `.local/pgdata`; local service bound to `127.0.0.1:55432`.
- Matching local backend/.env and frontend/.env.local files created, with mock mode and tracing disabled. Real API secrets remain blank.
- Two synthetic demonstration analyses are saved; they are real locally generated offline outputs. The same candidate was tested against AI/ML Intern (63.33) and Frontend Developer Intern (11.11).

Docker Desktop was present but failed to start due to its inference-manager listener initialization. The portable PostgreSQL instance was used instead. No alternate database was introduced.

The system `python` command pointed to an unusable Windows Store stub. Use `.venv\Scripts\python.exe` directly. A reproducible dependency snapshot is in backend/requirements.lock.txt; frontend/package-lock.json records frontend resolution.

## Run tomorrow

```powershell
cd D:\gen_ai_aat
.\start.ps1
```

Open http://localhost:3000. If you add keys or change backend/.env, use `.\start.ps1 -Restart`. This restarts only a backend process whose saved PID and executable belong to this launcher. Local logs are in `.local`.

Read SETUP.md for separate-terminal commands, fresh installation, PostgreSQL, API keys and deployment. Read DEMO.md for the six-minute speaking script, and CareerPilot_AI_Presentation_Guide.pdf for the detailed explanation.

## Limits to explain honestly

This is a local single-user application without authentication, per-user authorization, public deployment infrastructure, durable background execution or OCR. Mock mode has finite vocabulary and conservative interpretation. Compatibility weights are heuristics, not trained hiring probabilities. Evidence quotes and a separate review do not guarantee truth. Only synthetic documents should be used for full trace-payload inspection. Original binaries are not stored, but extracted resume text and result data are persisted until deletion.

Section edits/regeneration are reviewed once and can be marked manual_review; the initial full analysis uses the bounded two-revision graph loop. Application statuses are user-managed, and nothing is automatically submitted or emailed.

## Source readability cleanup

All frontend source and frontend configuration files are formatted with Prettier. Python application, migration, test and script files are formatted with Ruff. Grouped TypeScript variables use individual declarations, CSS properties and JSX components are expanded, and the PowerShell launcher uses readable parameter blocks.

Prettier and Ruff format checks, Ruff lint, PowerShell syntax, frontend type checking and the production build passed after cleanup. VS Code settings and extension recommendations support format on save. Private environment files were left unchanged.

LangSmith configuration now supports region endpoints, explicit workspace IDs and newer agent-based routing while retaining project-based setup. Two additional offline tests verify that project and agent destinations do not conflict. Cloud LangSmith and Neon account connections remain untested without credentials.

See ENVIRONMENT_AND_CONNECTIONS.md for all environment values, LangSmith steps, and Neon SQLAlchemy versus Prisma URL examples.
