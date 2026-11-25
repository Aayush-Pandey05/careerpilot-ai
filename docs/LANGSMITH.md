# LangSmith tracing and evaluation

LangSmith observes the running graph. Uploading Python source to GitHub does not execute or host FastAPI. The running backend sends traces with the configured API key.

For every environment value, Neon connection instructions, and the newer agent-based LangSmith interface, see [Environment values and connections](ENVIRONMENT_AND_CONNECTIONS.md). The project-based steps below apply when your workspace exposes Tracing Projects. In an agent-based workspace, register the existing application and configure its agent identifier as explained in that guide.

## Connect tracing

1. Visit [LangSmith](https://smith.langchain.com/) and create/sign into an account. Select your workspace.
2. Open Settings (gear icon), then API Keys. Create an API key with the required workspace access and copy it privately. Navigation labels can differ by workspace/UI release.
3. Open Tracing Projects. Create a project named `careerpilot-ai-dev` if the UI offers project creation. Otherwise the first traced run with this project name creates the project.
4. Edit `backend/.env` locally:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_private_langsmith_key
LANGSMITH_PROJECT=careerpilot-ai-dev
LANGSMITH_HIDE_INPUTS=true
LANGSMITH_HIDE_OUTPUTS=true
```

5. From the workspace root, run `.\start.ps1 -Restart` to restart the backend with the new settings. If you launched it in a terminal instead, stop it with Ctrl+C and relaunch it.
6. Run a synthetic resume/job analysis through the frontend. Wait for completion and trace upload.
7. Open Tracing Projects > `careerpilot-ai-dev`. Open the latest CareerPilot Analysis run.
8. Expand parsing, resume_analyzer, jd_analyzer, matching, generation, review and finalize nodes. Expand each nested operation to inspect its duration/status and tools. In live mode expand ChatOpenAI calls for model and token details when available. Related model calls are absent in offline mode.
9. Look for repeated generation/review nodes on revised runs. Use error/status filters to find failed nested operations. A handled node may succeed at the wrapper level while its operation failed; workflow state/events expose that failure too.
10. For full prompt/response inspection, use **synthetic documents only** and set both hide flags false, then restart and create a new run. This change affects future traces, not old hidden payloads. Restore both flags for real data or disable tracing.

Inputs/outputs are hidden by default at the SDK level, including tool arguments. Metadata includes mode/version, not personal names. Disabling tracing does not prevent live mode from sending document text to OpenAI. There is no claim of full PII anonymization.

## Create the evaluation dataset

From the backend folder with a configured LangSmith key:

```powershell
..\.venv\Scripts\python.exe -m scripts.create_langsmith_dataset
```

This creates `careerpilot-synthetic-v1` with ten synthetic cases. The script stops if that name already exists instead of duplicating data. Cases cover strong/weak matches, missing preferred and mandatory skills, transferability, missing projects, incomplete information, ambiguity, an injected unsupported claim and malicious job instructions.

## Run experiments

```powershell
..\.venv\Scripts\python.exe -m scripts.run_langsmith_evaluation --local
..\.venv\Scripts\python.exe -m scripts.run_langsmith_evaluation
```

The first command runs local checks only. The second uploads a real experiment and requires a LangSmith key. Its mode follows LLM_MODE; live mode also requires OpenAI credentials and incurs API use. Concurrency is set to 1 to control experiment cost and simplify inspection.

Open Datasets & Experiments > careerpilot-synthetic-v1. Open the experiment and inspect per-example results. Select two experiments to compare changes. Check failing rows, their intermediate trace and source evidence before changing prompts or weights. Compare like modes; live semantic reasoning may legitimately differ from narrow offline score expectations, so review failures instead of treating offline gold ranges as universal truth.

Code evaluators check workflow completion, candidate name, required-skill extraction, expected score ranges, arithmetic, quote grounding, role relevance and revision recovery. These are regression checks, not a comprehensive benchmark. Grammar, nuanced truthfulness, extraction completeness and practical resume quality still need annotated human evaluation. No LLM judge or large-scale benchmark is claimed.

Cloud tracing/evaluations need actual credentials. See VERIFICATION.md for what was executed locally.

## Official references

- [Trace privacy switches](https://docs.langchain.com/langsmith/mask-inputs-outputs)
- [Evaluation SDK workflow](https://docs.langchain.com/langsmith/evaluate-llm-application)
- [LangGraph graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
