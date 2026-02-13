from __future__ import annotations

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .ast_analyzer import analyze_repository
from .config import ARTIFACTS_DIR
from .git_refactor import GitRefactorError, create_refactor_commit
from .github_app import (
    GithubAppError,
    create_pr as create_github_pr,
    get_installation_token_from_env,
    is_github_app_configured,
    push_branch,
)
from .pr_draft import write_local_pr_draft
from .repo_ingest import RepoIngestError, ingest_repository
from .schemas import (
    AnalysisResultResponse,
    AnalysisRunRequest,
    AnalysisRunResponse,
    GithubPrRequest,
    GithubPrResponse,
    Hotspot,
    RefactorApplyRequest,
    RefactorApplyResponse,
    RefactorProposalRequest,
    RefactorProposalResponse,
    RepoImportRequest,
    RepoImportResponse,
)
from .store import store

app = FastAPI(title="Codebase Agent API", version="0.1.0")
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/repos/import", response_model=RepoImportResponse)
def import_repo(payload: RepoImportRequest) -> RepoImportResponse:
    repo_id = f"r_{uuid.uuid4().hex[:8]}"
    try:
        ingest_result = ingest_repository(payload.repo_url, payload.branch)
    except RepoIngestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    store.repos[repo_id] = {
        "repo_url": payload.repo_url,
        "branch": payload.branch,
        "path": ingest_result["path"],
        "commit_sha": ingest_result["commit_sha"],
        "status": "completed",
    }
    return RepoImportResponse(repo_id=repo_id, commit_sha=ingest_result["commit_sha"], status="completed")


@app.post("/analysis/run", response_model=AnalysisRunResponse)
def run_analysis(payload: AnalysisRunRequest) -> AnalysisRunResponse:
    repo = store.repos.get(payload.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="repo_id not found")
    analysis_id = f"a_{uuid.uuid4().hex[:8]}"
    analysis_data = analyze_repository(repo["path"], analysis_id)
    store.analyses[analysis_id] = {
        "repo_id": payload.repo_id,
        "commit_sha": repo["commit_sha"] if payload.commit_sha == "HEAD" else payload.commit_sha,
        **analysis_data,
    }
    return AnalysisRunResponse(analysis_id=analysis_id, status="completed")


@app.get("/analysis/{analysis_id}", response_model=AnalysisResultResponse)
def get_analysis(analysis_id: str) -> AnalysisResultResponse:
    item = store.analyses.get(analysis_id)
    if not item:
        raise HTTPException(status_code=404, detail="analysis_id not found")
    hotspots = [Hotspot(**h) for h in item["hotspots"]]
    return AnalysisResultResponse(
        status=item["status"],
        summary=item["summary"],
        hotspots=hotspots,
        module_graph_url=item["module_graph_url"],
    )


@app.post("/refactors/propose", response_model=RefactorProposalResponse)
def propose_refactor(payload: RefactorProposalRequest) -> RefactorProposalResponse:
    analysis = store.analyses.get(payload.analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="analysis_id not found")
    proposal_id = f"p_{uuid.uuid4().hex[:8]}"
    files = [hotspot["file"] for hotspot in analysis["hotspots"][: payload.max_changes]]
    if not files:
        files = ["README.md"]
    store.proposals[proposal_id] = {
        "analysis_id": payload.analysis_id,
        "scope": payload.scope,
        "max_changes": payload.max_changes,
        "title": "Extract validation layer",
        "risk": "low",
        "files": files,
    }
    return RefactorProposalResponse(
        proposal_id=proposal_id,
        title="Extract validation layer",
        risk="low",
        files=files,
    )


@app.post("/refactors/apply", response_model=RefactorApplyResponse)
def apply_refactor(payload: RefactorApplyRequest) -> RefactorApplyResponse:
    proposal = store.proposals.get(payload.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="proposal_id not found")
    analysis = store.analyses.get(proposal["analysis_id"])
    if not analysis:
        raise HTTPException(status_code=404, detail="analysis not found for proposal")
    repo = store.repos.get(analysis["repo_id"])
    if not repo:
        raise HTTPException(status_code=404, detail="repo not found for analysis")

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    head_branch = f"codebase-agent/{payload.proposal_id}"
    try:
        commit_data = create_refactor_commit(
            repo_path=repo["path"],
            base_branch=repo["branch"],
            head_branch=head_branch,
            proposal_id=payload.proposal_id,
            files=proposal["files"],
        )
    except GitRefactorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store.runs[run_id] = {
        "proposal_id": payload.proposal_id,
        "run_tests": payload.run_tests,
        "status": "completed",
        "head_branch": commit_data["head_branch"],
        "commit_sha": commit_data["commit_sha"],
    }
    return RefactorApplyResponse(run_id=run_id, status="completed")


@app.post("/github/pr", response_model=GithubPrResponse)
def create_pr(payload: GithubPrRequest) -> GithubPrResponse:
    run = store.runs.get(payload.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_id not found")
    repo = store.repos.get(payload.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="repo_id not found")
    if run["status"] != "completed":
        raise HTTPException(status_code=400, detail="run is not completed")
    if payload.head_branch != run.get("head_branch"):
        raise HTTPException(status_code=400, detail="head_branch must match run head_branch")

    if not is_github_app_configured():
        draft_url = write_local_pr_draft(
            run_id=payload.run_id,
            repo_url=repo["repo_url"],
            base=payload.base,
            head_branch=payload.head_branch,
            title=payload.title,
            body=payload.body,
            commit_sha=run.get("commit_sha", ""),
        )
        return GithubPrResponse(pr_url=draft_url, status="skipped")

    try:
        token = get_installation_token_from_env()
        push_branch(repo_path=repo["path"], repo_url=repo["repo_url"], head_branch=payload.head_branch, token=token)
        pr_url = create_github_pr(
            repo_url=repo["repo_url"],
            base=payload.base,
            head_branch=payload.head_branch,
            title=payload.title,
            body=payload.body,
        )
    except GithubAppError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GithubPrResponse(pr_url=pr_url, status="opened")
