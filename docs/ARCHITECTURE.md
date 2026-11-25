# Architecture

The app has one backend. Next.js renders the user interface and calls FastAPI over HTTP. FastAPI validates uploads, runs LangGraph and persists completed results in PostgreSQL using SQLAlchemy 2.x. Alembic records schema migrations. The graph has five AI specialists plus deterministic parsing and finalization nodes; the orchestrator is code, not a sixth LLM agent.

## Responsibilities and access

| Agent | Inputs | Outputs | Allowed operations |
|---|---|---|---|
| Resume Analyzer | Extracted resume text | ResumeProfile | Structured extraction; no disk/shell access |
| Job Description Analyzer | Job text, optional role/company | JobProfile | Structured requirement extraction |
| Resume Matching | Original text, resume/job profiles | Evidence rows, explanations, scoring breakdown | Skill matcher, centralized score calculator |
| Application Generator | Source facts, job, matching, reviewer feedback | ApplicationMaterials and claim ledger | Draft content only |
| Review Agent | Original source, job, generated material | ReviewReport | Fact comparison and conservative rule checks |

Live agents use individual instructions and Pydantic schemas. They are bounded specialists in an agentic workflow, not independently autonomous web-browsing agents. Tools are explicitly called by their node's code, rather than exposing arbitrary tool selection to the LLM. This keeps capabilities restricted and calculations reproducible.

## State and routing

`WorkflowState` holds transient file bytes, original extracted text, job text, both profiles, matching results, materials, review, revision count, errors and lifecycle events. Agents return partial updates. `events` and `errors` use additive reducers so parallel writes combine. The profile fields have a single writer each.

Parsing fans out to resume and job analysis in one graph superstep. A list-based join edge waits for both before matching. Generation passes the current draft to review. Approval ends the run. Rejection sends feedback to generation if `revision_count < MAX_REVISION_ATTEMPTS`. The first draft has count 0; two revisions allow at most three generator and three reviewer executions. Failure routes to finalization with a failed status and partial results.

SSE events are emitted inside the actual node wrapper at start, completion or failure. FastAPI streams those events through an async queue to the frontend. It emits workflow completion only after the database commit succeeds. Disconnection cancels the running task. No queue, external worker or graph checkpoint store is claimed.

## Evidence and scoring

Matching constructs the full required requirement list centrally. Live semantic outputs are reconciled to that list; invented extra rows are ignored, omitted rows become Cannot Determine, and positive matches without a verbatim source quote become Cannot Determine. A quote's existence is a grounding check, not proof that the semantic interpretation is correct.

Scores use arithmetic only in `score_calculator.py`. Category coverage is sum of status credits divided by number of requirements. Credits are Direct=1, Related=0.5, Partial=0.25, Missing=0 and Cannot Determine=0. The final score is 100 times the weighted average. No protected personal attributes enter the score.

Example: mandatory coverage 4/5=0.8, preferred coverage 1/2=0.5 and alignment 1/2=0.5 yields `100*(0.7*0.8 + 0.2*0.5 + 0.1*0.5)=71`. If alignment has no requirements, use `100*(0.7*0.8+0.2*0.5)/0.9=73.33`. Missing categories are not assumed perfect. No requirements yields null.

Offline matching recognizes a finite skill vocabulary and common aliases. A few directed related-skill mappings give only partial credit; PyTorch and TensorFlow remain different skills. Natural-language years/responsibilities that cannot be established receive Cannot Determine. This conservative path is labeled mock mode.

## Validation and persistence

File extension, magic bytes, byte size, expanded DOCX size, PDF page count, text length and readability are checked. Parsing occurs in memory with PyMuPDF/python-docx. No OCR is performed.

Four tables: `analyses`, `resume_profiles`, `analysis_results`, `applications`. The analysis owns one of each linked record. ORM cascades and database foreign keys support full deletion. A single transaction saves the result. No original PDF/DOCX is stored. Source text is stored separately from browser responses for subsequent validation. The UI shows derived data and evidence.

Editing/regeneration affects only the requested prose section and triggers review again; it never repeats extraction or scoring. The final workflow review may be replaced by that latest review, while the original execution events and revision count remain historical. Review quality is a heuristic or model judgment, separate from deterministic compatibility.

## Reliability and tracing

OpenAI client has bounded transient retries and a request timeout. There is no retry of an entire workflow on an API error. A second hard guard uses graph recursion limit 30. Errors exposed to clients are generic and omit provider bodies and credentials. Nested traceable operations record failures even when the node wrapper converts them into failed workflow state. Parsing/matching/scoring tools have trace names. LangChain captures model call metadata when supported.

Default trace inputs/outputs are hidden globally. Do not enable payload traces for real resumes. Review factual accuracy, privacy retention, rate limits and authentication before public use.
