# Codebase Agent

[![CI](https://github.com/mozaika228/codebaseagent/actions/workflows/ci.yml/badge.svg)](https://github.com/mozaika228/codebaseagent/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-pytest-blue)
![Coverage](https://img.shields.io/badge/coverage-ci%20artifact-important)

AI agent monorepo for repository ingestion, architecture understanding, safe refactor proposals, and draft PR generation.

## Why this repo

This project targets practical autonomous code improvement with guardrails:

- real git ingest and commit pinning
- AST-backed analysis and hotspot extraction
- scoped refactor proposal and apply flow
- GitHub App draft PR publishing with fallback mode
- eval-friendly metrics and artifacts

## What works right now

- Backend API (`apps/api`)
- `POST /repos/import` with real clone/fetch
- `POST /analysis/run` with Python AST and JS/TS best-effort parsing
- `POST /refactors/propose` and `POST /refactors/apply`
- `POST /github/pr`:
- opens draft PR via GitHub App when configured
- writes local PR draft artifact when app creds are missing

- Frontend (`apps/web`)
- pipeline UI: import -> analysis -> proposal -> apply -> PR
- RAG workspace UI: chat panel, document upload list, result summary, answer compare table

- CI
- API tests with coverage gate
- web typecheck and production build

## Sample API flow

1. Import repo

```bash
curl -X POST http://localhost:8000/repos/import ^
  -H "Content-Type: application/json" ^
  -d "{\"repo_url\":\"https://github.com/org/repo\",\"branch\":\"main\"}"
```

2. Run analysis

```bash
curl -X POST http://localhost:8000/analysis/run ^
  -H "Content-Type: application/json" ^
  -d "{\"repo_id\":\"r_123\",\"commit_sha\":\"HEAD\"}"
```

3. Propose and apply refactor, then draft PR

```bash
curl -X POST http://localhost:8000/refactors/propose -H "Content-Type: application/json" -d "{\"analysis_id\":\"a_123\",\"scope\":[\"src/**\"],\"max_changes\":5}"
curl -X POST http://localhost:8000/refactors/apply -H "Content-Type: application/json" -d "{\"proposal_id\":\"p_123\",\"run_tests\":true}"
curl -X POST http://localhost:8000/github/pr -H "Content-Type: application/json" -d "{\"run_id\":\"run_123\",\"repo_id\":\"r_123\",\"base\":\"main\",\"head_branch\":\"codebase-agent/p_123\"}"
```

## Quickstart

### API

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Worker

```bash
cd apps/worker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m worker.main
```

### Web

```bash
cd apps/web
pnpm install
pnpm dev
```

## Testing and CI

Run API tests locally:

```bash
cd apps/api
pip install -r requirements.txt
pytest tests -q --cov=app --cov-report=term
```

CI workflow: `.github/workflows/ci.yml`

- API tests + coverage XML artifact upload
- Web typecheck (`tsc --noEmit`)
- Web build (`next build`)

## Demo

- Screenshots: `docs/demo/` (add your latest UI screenshots here)
- Video demo: add link in this section

## Roadmap

1. Implement true RAG retrieval pipeline and source citations in UI
2. Add semantic/code graph indexing for multi-language repos
3. Add patch-level diff viewer in web app
4. Add evaluator dashboard with trend charts (accuracy, latency, cost)
5. Add human review workflow (approve/reject/edit before PR)

## Project structure

- `apps/api` FastAPI service
- `apps/worker` orchestration worker scaffold
- `apps/web` Next.js UI
- `packages/shared-types` contracts/schemas
- `packages/prompt-templates` prompts
- `packages/evals` metrics tables and eval docs
- `docs` ADR/API/eval notes

## License

This project is licensed under MIT. See `LICENSE`.

## Contributing

See `CONTRIBUTING.md`.
