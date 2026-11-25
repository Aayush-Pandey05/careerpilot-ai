# Six minute classroom demonstration

Before class: start PostgreSQL, apply migrations, launch FastAPI and Next.js, open the UI and API docs, and keep a terminal ready. Use synthetic data only. Complete one rehearsal in mock mode; if you plan to show live reasoning, verify your model/key/billing tonight. Keep a local screenshot or PDF of real results as backup, clearly labeled saved output.

## Minute 0 to 1 Explain the problem and architecture

Say: Students repeatedly compare the same resume with different jobs. CareerPilot separates understanding, comparison, writing and verification into five focused agents. Next.js is the interface; one FastAPI backend performs the workflow. PostgreSQL saves results, OpenAI supplies language reasoning in live mode, and LangSmith observes execution.

Show the overview. Explain that dashboard counts come from saved analyses. Explicitly state whether the run is offline mock or live AI.

## Minute 1 to 2 Upload and run

Open New analysis. Download the provided sample PDF, upload it, click Use sample role and run. Explain the parser extracts text before the two analysis agents run in parallel. Show actual lifecycle events; offline runs can finish too quickly to watch, so open Agent workflow afterwards.

Say: The Resume Analyzer extracts the candidate facts. The Job Description Analyzer separates mandatory and preferred requirements. Both use structured outputs in live mode, so later agents receive predictable data.

## Minute 2 to 3 Explain matching

Open results and the evidence table. Point to Python as a direct match, Docker as partial, PyTorch as transferable evidence for TensorFlow, and AWS as missing when shown by the sample. The offline matcher may mark natural language education/responsibilities unknown; explain its limits.

Say: The model can interpret meaning, but Python calculates the numerical score. A direct match receives one credit; related half; partial one quarter; missing and unknown zero. Mandatory/preferred/alignment base weights are 70/20/10. The percentage measures documented compatibility, not hiring probability.

## Minute 3 to 4 Show applications and validation

Open Application studio, edit an email, save and review, copy or download it, then download the report. Explain that edits are re-reviewed and the system never emails employers. Open Interview prep and show questions about the candidate projects and skill gaps.

Say: The generator sees verified source material and the reviewer checks it independently. Two revisions are allowed. A third rejected draft ends in manual review instead of pretending success.

## Minute 4 to 5 Show actual test evidence

Run the two conditional tests from TESTING.md, then run `python -m pytest -v` if time permits. Show the actual outcome on screen. Explain that one test injects a false claim and verifies recovery; another rejects every draft and verifies termination. Distinguish unit tests from integration tests and coverage from quality.

## Minute 5 to 6 Show tracing and comparison

If credentials are configured, open LangSmith > Tracing Projects > careerpilot-ai-dev, expand a real run, show model/tool calls and repeated generation/review nodes when present. If not configured, show the graph and local timeline, and say cloud tracing has been implemented but not verified with credentials.

Re-run the same resume for a different job, such as a frontend role requiring JavaScript, React and CSS. Open history and compare compatibility; each run remains linked to the same candidate name and its specific role. Update an application status manually.

Close by saying: The main contribution is a transparent workflow with evidence-based scoring and bounded review. Its limits include imperfect extraction and model reasoning, heuristic weights, and the need for human review and deployment security.

## Questions to rehearse

Use PRESENTATION_GUIDE.md or its PDF. Be ready to explain why parallel analysis is safe, what state reducers do, how two revisions differ from two API retries, why structured output is not factual verification, what data is stored, and why model training hyperparameters do not apply to an API inference workflow.
