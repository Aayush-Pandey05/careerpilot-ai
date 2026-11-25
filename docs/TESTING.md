# Testing and interpretation

Tests execute real functions and the real StateGraph. They use synthetic documents and do not require OpenAI or LangSmith keys.

```powershell
cd D:\gen_ai_aat\backend
..\.venv\Scripts\python.exe -m pytest -v
..\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
..\.venv\Scripts\python.exe -m scripts.run_langsmith_evaluation --local
```

Unit tests cover PDF/DOCX parsing, corrupt/empty/oversized uploads, skill aliases and boundaries, partial/related classifications, deterministic arithmetic, extraction, prompt injection as data, malformed structured output, configuration validation and unsupported claim detection.

Graph integration tests establish that both analysis branches enter before either is allowed to complete. This proves concurrent graph scheduling instead of relying on a fast timing guess. Other tests prove the matching join waits for both outputs, the whole workflow completes, provider errors become safe failure state, unsupported generated content can trigger one revision, and repeated rejection terminates after exactly two revisions.

API tests cover health degradation, invalid uploads, missing job data and CORS. Full PostgreSQL integration covers analysis creation/reopening, list/history, PDF download, status changes, invalid statuses, editing and re-review, and linked-record deletion.

## Enable PostgreSQL integration

Use a dedicated test database, never one holding personal data. The fixture creates an isolated temporary schema and rolls back test data. The user needs permission to create schemas. The test does not use SQLite.

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://careerpilot:careerpilot_local@localhost:5432/careerpilot'
..\.venv\Scripts\python.exe -m pytest -v
Remove-Item Env:TEST_DATABASE_URL
```

Without TEST_DATABASE_URL the database test is skipped and reported as skipped. Passing offline graph tests is not proof of database connectivity. Use Alembic against a local database separately to verify migrations, then GET /api/v1/health and a real upload.

## Conditional routing demonstration

```powershell
..\.venv\Scripts\python.exe -m pytest tests/integration/test_workflow.py -k "injected or revision_limit" -v
```

The controlled generator adds a false AWS/99% statement only on draft zero. The actual reviewer rejects it. The next draft removes the claim and passes. A separate rejecting reviewer tests all three drafts, revision counts [0,1,2], and manual_review status. These hooks exist in Python test dependency injection, not in a production upload switch.

## Frontend checks

```powershell
cd D:\gen_ai_aat\frontend
npm.cmd run typecheck
npm.cmd run build
```

Webpack is used because this Windows runtime encountered a Turbopack CSS worker crash. This changes the build engine, not the application architecture. Manually inspect desktop/mobile navigation, upload validation, live lifecycle events, results, edits, report downloads, status updates and deletion. No automated browser test suite is claimed.

Coverage shows executed code, not correctness or model quality. Read the missed-line report before increasing coverage. Live OpenAI and LangSmith are separate external checks and require your credentials. Never label them verified just because the offline suite passes. Actual results and environment limits are recorded in VERIFICATION.md.
