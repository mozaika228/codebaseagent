# Codebase Agent MVP

Monorepo for an AI agent that understands a repository, proposes safe refactors, and drafts pull requests.

## Stack

- Monorepo: pnpm + turbo
- Backend API: FastAPI
- Workflow orchestration: LangGraph-style worker scaffold
- Frontend: Next.js App Router
- Optional local models: Ollama

## Repository Layout

- `apps/api`: FastAPI service exposing ingest, analysis, refactor, and PR endpoints
- `apps/worker`: orchestration and sandbox test runner stubs
- `apps/web`: Next.js UI for repository import and run tracking
- `packages/shared-types`: shared JSON schemas/contracts
- `packages/prompt-templates`: prompt templates used by agents
- `packages/evals`: metrics schema and starter dataset
- `docs`: ADRs, API notes, and eval methodology

## Quickstart

### 1) API

```bash
cd apps/api
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Optional for GitHub App PR creation:

```bash
set GITHUB_APP_ID=...
set GITHUB_APP_INSTALLATION_ID=...
set GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----...
```

### 2) Worker

```bash
cd apps/worker
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python -m worker.main
```

### 3) Web

```bash
cd apps/web
pnpm install
pnpm dev
```

## Tests

```bash
cd apps/api
pip install -r requirements.txt
pytest tests -q
```

## CI

GitHub Actions workflow is at `.github/workflows/ci.yml`.
It runs:

- API tests (`pytest`)
- Web typecheck (`tsc --noEmit`)
- Web production build (`next build`)

## MVP API Contract

- `POST /repos/import`
- `POST /analysis/run`
- `GET /analysis/{analysis_id}`
- `POST /refactors/propose`
- `POST /refactors/apply`
- `POST /github/pr`

`/repos/import` performs real clone/fetch.
`/analysis/run` performs AST-backed analysis for Python and JS/TS files.
`/refactors/apply` creates a real commit in a `codebase-agent/*` branch.
`/github/pr` pushes that branch and opens a draft PR via GitHub App.
If `GITHUB_APP_*` is missing, `/github/pr` falls back to local draft mode and returns `status=skipped`.

## Evals

Track these for every run:

- task_success_rate
- ci_pass_rate
- human_acceptance_rate
- regression_rate
- latency_p50 / latency_p95
- cost_per_successful_pr
- hallucination_rate
