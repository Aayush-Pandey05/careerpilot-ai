# Environment values and service connections

There are two environment files, not an environment folder:

- `backend/.env`: private configuration read by FastAPI, agents and database tools.
- `frontend/.env.local`: the public FastAPI address used by the browser.

Both already exist in the prepared workspace. Edit them in your IDE. Do not overwrite your real keys or paste them into chat. `.env.example` is a documented template, not the file your running backend reads.

## Values for the prepared local application

Keep this frontend value:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

The following backend template runs offline with the portable PostgreSQL database already created on this computer:

```env
OPENAI_API_KEY=
OPENAI_MODEL=
LLM_MODE=mock

LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=careerpilot-ai-dev
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_WORKSPACE_ID=
LANGSMITH_AGENT_ID=
LANGSMITH_AGENT_ENVIRONMENT=development
LANGSMITH_HIDE_INPUTS=true
LANGSMITH_HIDE_OUTPUTS=true

DATABASE_URL=postgresql+psycopg://careerpilot:careerpilot_local@127.0.0.1:55432/careerpilot
APP_ENV=development
MAX_REVISION_ATTEMPTS=2
MAX_UPLOAD_MB=10
MAX_TEXT_CHARS=40000
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=2
LLM_MAX_TOKENS=6000
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

Do not use the sample local password for a public database. Your Neon URL will contain the actual Neon role and password, not this local account.

## Meaning of every variable

| Variable                      | Value to use                                                                                                                 | Meaning                                                                                                                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OPENAI_API_KEY`              | Blank for mock; your private OpenAI API key for live                                                                         | Authenticates model requests. Create it at https://platform.openai.com/api-keys.                                                                     |
| `OPENAI_MODEL`                | Blank for mock; for example `gpt-4.1-mini` if available to your API project                                                  | A structured-output-capable API model. This example is supported by the official model documentation; your project must have access and API billing. |
| `LLM_MODE`                    | `mock` initially; `live` after configuring OpenAI                                                                            | Selects deterministic offline components or real model calls.                                                                                        |
| `LANGSMITH_TRACING`           | `false` initially; `true` to send traces                                                                                     | Enables observability independently of OpenAI mode.                                                                                                  |
| `LANGSMITH_API_KEY`           | Your LangSmith key when tracing/evaluating                                                                                   | Separate from the OpenAI key. A PAT or suitable service key can also create evaluation datasets; a tracing-only key cannot run experiments.          |
| `LANGSMITH_PROJECT`           | `careerpilot-ai-dev` for project-based workspaces                                                                            | Groups workflow traces. For agent-based addressing, the app omits this legacy destination automatically.                                             |
| `LANGSMITH_ENDPOINT`          | `https://api.smith.langchain.com` for default US; use the endpoint shown by your workspace's setup screen for another region | The tracing API address, not the browser dashboard URL. For EU, the documented endpoint is `https://eu.api.smith.langchain.com`.                     |
| `LANGSMITH_WORKSPACE_ID`      | Blank when unneeded; otherwise your actual workspace ID                                                                      | Required if the key's scope needs an explicit workspace. Copy it from LangSmith workspace settings/setup.                                            |
| `LANGSMITH_AGENT_ID`          | Blank in a project-based workspace; actual registered agent identifier in an agent-based workspace                           | The new LangSmith destination format. It is not the display name of one of our five Python specialists.                                              |
| `LANGSMITH_AGENT_ENVIRONMENT` | `development`                                                                                                                | Used only with an agent ID. Other accepted values: `local`, `staging`, `production`.                                                                 |
| `LANGSMITH_HIDE_INPUTS`       | `true` for personal resumes                                                                                                  | Hides traced inputs. Set `false` only when inspecting synthetic examples.                                                                            |
| `LANGSMITH_HIDE_OUTPUTS`      | `true` for personal resumes                                                                                                  | Hides traced outputs. Hiding inputs alone does not hide generated personal information.                                                              |
| `DATABASE_URL`                | Prepared local URL above, or your adapted Neon URL below                                                                     | Where SQLAlchemy/psycopg connects. Includes credentials and stays on the backend.                                                                    |
| `APP_ENV`                     | `development` locally                                                                                                        | Application environment label; does not add production security automatically.                                                                       |
| `MAX_REVISION_ATTEMPTS`       | `2`                                                                                                                          | At most two content revisions after the original draft. Allowed range 0 to 2.                                                                        |
| `MAX_UPLOAD_MB`               | `10`                                                                                                                         | Resume upload limit in MB.                                                                                                                           |
| `MAX_TEXT_CHARS`              | `40000`                                                                                                                      | Maximum extracted resume/job text length.                                                                                                            |
| `LLM_TIMEOUT_SECONDS`         | `60`                                                                                                                         | Timeout for each model request.                                                                                                                      |
| `LLM_MAX_RETRIES`             | `2`                                                                                                                          | Bounded transient API retries, separate from content revisions.                                                                                      |
| `LLM_MAX_TOKENS`              | `6000`                                                                                                                       | Output-token limit per model call, not a total workflow budget.                                                                                      |
| `CORS_ORIGINS`                | JSON array shown above                                                                                                       | Browser frontend origins allowed to call FastAPI. Keep the JSON syntax.                                                                              |
| `NEXT_PUBLIC_API_URL`         | `http://localhost:8000/api/v1` for this local frontend                                                                       | Public backend address. Never put a secret in a `NEXT_PUBLIC_` variable.                                                                             |

For live AI, change only these OpenAI values first:

```env
OPENAI_API_KEY=your_actual_private_openai_key
OPENAI_MODEL=gpt-4.1-mini
LLM_MODE=live
```

`gpt-4.1-mini` is an example, not a claim that your account has already been tested. You may select another API model that supports structured outputs. API billing is separate from a ChatGPT subscription. Official reference: https://developers.openai.com/api/docs/models/gpt-4.1-mini.

## Connect LangSmith step by step

1. Sign into https://smith.langchain.com and choose your workspace.
2. Open **Settings > API Keys** and create a PAT for your personal demo, or a suitable workspace-scoped service key. Copy it locally into `LANGSMITH_API_KEY`. Do not use the OpenAI key here.
3. Identify the interface your workspace uses:
   - **Project-based:** open **Tracing Projects**, create/use `careerpilot-ai-dev`, leave `LANGSMITH_AGENT_ID` blank, and keep `LANGSMITH_PROJECT=careerpilot-ai-dev`. A first run may create the project when your key has permission.
   - **Agent-based:** choose **+ Agent > Observability / Trace an existing agent**. Register the existing CareerPilot application, choose/copy its immutable identifier (for example `careerpilot-ai-dev`), set `LANGSMITH_AGENT_ID` to it and `LANGSMITH_AGENT_ENVIRONMENT=development`. The backend suppresses `LANGSMITH_PROJECT` in this mode to avoid competing destinations. This is a tracing record, not a new deployed application or a replacement for our five Python agents.
4. Set `LANGSMITH_TRACING=true`. Set the endpoint for the account's region and workspace ID if its setup instructions require one.
5. Keep the hide flags true for real resumes. For a synthetic classroom demonstration, you can set both false to inspect prompts and outputs.
6. Restart FastAPI from the workspace root:

```powershell
cd D:\gen_ai_aat
.\start.ps1 -Restart
```

7. Upload the provided synthetic resume and run an analysis. It works with tracing even in mock mode, but only live mode contains actual OpenAI calls.
8. In LangSmith, open either the project or your registered agent's **Development** tracing environment. Open the latest **CareerPilot Analysis** run. Expand parser, resume analyzer, job analyzer, matching, generation, review and their nested operations. Check timings and error statuses.
9. For evaluations, use a PAT/service key with dataset and experiment permissions, then run from `backend`:

```powershell
..\.venv\Scripts\python.exe -m scripts.create_langsmith_dataset
..\.venv\Scripts\python.exe -m scripts.run_langsmith_evaluation
```

If traces are missing, check restart, selected workspace/environment, API endpoint region, key permissions and whether a workflow actually ran. A tracing-enabled flag in the UI confirms configuration, not successful cloud ingestion. Agent-based routing requires the SDK version in the supplied lock file. Remove old `LANGCHAIN_PROJECT`/`LANGCHAIN_SESSION` destination overrides if you previously set them in your shell.

Official references: https://docs.langchain.com/langsmith/create-account-api-key, https://docs.langchain.com/langsmith/trace-with-langchain, and https://docs.langchain.com/langsmith/create-an-agent.

## Get the correct Neon PostgreSQL URL

1. Sign into https://console.neon.tech and create/open a project.
2. Choose **Connect**. Select the branch, compute, database and database role you intend to use. The connection string is constructed from those selections.
3. For the simplest setup with this small FastAPI application, turn **Connection pooling off** and copy the direct PostgreSQL URL. The same direct URL can be used by the app and Alembic. Neon requires TLS; retain its `sslmode` and other psycopg-compatible security parameters.
4. Neon provides a URL shaped like this (every uppercase item is a placeholder):

```env
postgresql://ROLE:PASSWORD@ep-YOUR-ENDPOINT.REGION.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

5. For **this FastAPI + SQLAlchemy app**, change only the protocol prefix:

```env
DATABASE_URL=postgresql+psycopg://ROLE:PASSWORD@ep-YOUR-ENDPOINT.REGION.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

Copy your real complete string from Neon; do not invent a host or reuse the sample password. The database name is whatever you selected, not necessarily `neondb`. Leave any URL-encoding in the copied password intact. `prisma://` or `prisma+postgres://` is not a Neon PostgreSQL wire connection suitable for psycopg. Prisma-specific query parameters such as `schema`, `connection_limit` or `pgbouncer` should not be added to a psycopg connection URL.

6. Put the adapted string in **backend/.env**, replacing the local `DATABASE_URL`. Do not put it in frontend/.env.local.
7. Run the existing migrations against the selected Neon database:

```powershell
cd D:\gen_ai_aat\backend
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
.\start.ps1 -Restart
```

8. Open http://localhost:8000/api/v1/health and check `database: connected`, then upload a synthetic document and verify history. A successful SELECT 1 alone does not prove migrations were applied.

Changing DATABASE_URL changes where new data is stored. It does **not** copy existing local analyses into Neon. No Neon connection or data transfer has been performed without your credentials. The launcher may still start the existing local server; the backend nevertheless uses the URL configured in its environment file.

For a higher-concurrency deployment, Neon also supplies a pooled URL with `-pooler` in the hostname. Use direct connections for migrations/session-dependent operations. The current app has one database URL, so using a direct connection for both runtime and Alembic is the simplest initial configuration; separate runtime/migration URLs would be an explicit future configuration change.

Official reference: https://neon.com/docs/connect/connect-from-any-app.

## What changes if you use Prisma

Neon is the PostgreSQL hosting service. Prisma and SQLAlchemy are alternative ways for application code to query PostgreSQL. You do not need Prisma to connect this app to Neon. CareerPilot currently uses SQLAlchemy in Python and Alembic for schema migrations; the Next.js app is a frontend only.

For a **separate JavaScript/TypeScript application using Prisma**, the connection values usually look like this:

```env
DATABASE_URL=postgresql://ROLE:PASSWORD@ep-YOUR-ENDPOINT-pooler.REGION.aws.neon.tech/neondb?sslmode=require
DATABASE_URL_UNPOOLED=postgresql://ROLE:PASSWORD@ep-YOUR-ENDPOINT.REGION.aws.neon.tech/neondb?sslmode=require
```

The pooled URL is for runtime queries. The direct URL is for Prisma CLI operations. Copy both from the same Neon branch/database/role. Keep the normal `postgresql://` prefix for Prisma; the `+psycopg` addition is only for our Python SQLAlchemy driver. Use query parameters appropriate to the selected Prisma adapter, as shown in Neon's Prisma connection example.

In Prisma 7, `prisma.config.ts` supplies the CLI datasource URL:

```typescript
import 'dotenv/config';
import { defineConfig, env } from 'prisma/config';

export default defineConfig({
  schema: 'prisma/schema.prisma',
  datasource: {
    url: env('DATABASE_URL_UNPOOLED'),
  },
});
```

Its `schema.prisma` datasource declares the PostgreSQL provider without a URL property. Runtime queries use a Prisma client with the chosen PostgreSQL/Neon adapter and the pooled URL. Older Prisma 6 tutorials put `url` and `directUrl` in `schema.prisma`; that configuration should not be copied blindly into Prisma 7.

This Prisma snippet is a reference, not a new installed backend layer. Replacing SQLAlchemy with Prisma would require a deliberate rewrite of database services and migration ownership. Do not run Prisma migrations and Alembic independently against the same CareerPilot schema. If you only want Neon hosting, use the SQLAlchemy URL above and keep the existing architecture.

Official references: https://neon.com/docs/guides/prisma and https://www.prisma.io/docs/orm/v7/core-concepts/supported-databases/postgresql.

## Keep the source code formatted

The frontend now uses Prettier and the Python files use Ruff's formatter. JSX elements, attributes, CSS declarations, function arguments and object properties are expanded consistently. Grouped TypeScript variable declarations are split into individual statements.

VS Code workspace settings enable formatting on save. Install the recommended **Prettier**, **Ruff** and **Python** extensions when VS Code prompts, or install them from Extensions. Formatting commands also work without the editor extensions:

```powershell
cd D:\gen_ai_aat
npm.cmd run format --prefix frontend
.\.venv\Scripts\python.exe -m ruff format backend

npm.cmd run format:check --prefix frontend
.\.venv\Scripts\python.exe -m ruff format --check backend
```

Generated dependencies, lock-file internals and build output should not be manually reformatted. Your private environment files were left unchanged during this cleanup.
