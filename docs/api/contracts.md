# API Contracts

## Endpoints

- `POST /repos/import`
- `POST /analysis/run`
- `GET /analysis/{analysis_id}`
- `POST /refactors/propose`
- `POST /refactors/apply`
- `POST /github/pr`

## Notes

- `POST /repos/import` performs real `git clone/fetch` and returns `commit_sha`.
- `POST /analysis/run` runs AST analysis for Python and JS/TS files and builds `graph.json` artifact.
- `POST /refactors/apply` creates a real commit in `codebase-agent/<proposal_id>` branch.
- `POST /github/pr` pushes `head_branch` and opens a draft PR via GitHub App.
- If GitHub App env vars are missing, `POST /github/pr` returns `status=skipped` and stores a local draft at `/artifacts/pr-drafts/<run_id>.md`.

See `apps/api/app/schemas.py` for request and response models.