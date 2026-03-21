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
from .indexer.index_repo import index_repository
from .llm.ollama_client import chat, embed
from .memory.sqlite_memory import (
    add_feedback,
    add_message,
    complete_task,
    create_conversation,
    init_db,
    list_conversations,
    list_messages,
    enqueue_task,
    next_task,
)
from .pr_draft import write_local_pr_draft
from .repo_ingest import RepoIngestError, ingest_repository, install_post_commit_hook
from .schemas import (
    AnalysisResultResponse,
    AnalysisRunRequest,
    AnalysisRunResponse,
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    FeedbackRequest,
    FeedbackResponse,
    GithubPrRequest,
    GithubPrResponse,
    Hotspot,
    IndexRepoRequest,
    IndexRepoResponse,
    MessageHistoryResponse,
    RepoImportRequest,
    RepoImportResponse,
    RepoInfoResponse,
    RefactorApplyRequest,
    RefactorApplyResponse,
    RefactorProposalRequest,
    RefactorProposalResponse,
    TaskEnqueueRequest,
    TaskEnqueueResponse,
    TaskStatusResponse,
)
from .store import store
from .vector_store.chroma_store import ChromaStore

app = FastAPI(title="Codebase Agent API", version="0.2.0")
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")

init_db()


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

    try:
        install_post_commit_hook(ingest_result["path"], repo_id)
    except Exception:
        pass

    try:
        index_repository(repo_id, ingest_result["path"])
    except Exception:
        pass

    return RepoImportResponse(repo_id=repo_id, commit_sha=ingest_result["commit_sha"], status="completed")


@app.get("/repos/{repo_id}", response_model=RepoInfoResponse)
def get_repo(repo_id: str) -> RepoInfoResponse:
    repo = store.repos.get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="repo_id not found")
    return RepoInfoResponse(
        repo_id=repo_id,
        repo_url=repo["repo_url"],
        branch=repo["branch"],
        commit_sha=repo["commit_sha"],
        status=repo["status"],
        path=repo["path"],
    )


@app.post("/index/repo", response_model=IndexRepoResponse)
def index_repo(payload: IndexRepoRequest) -> IndexRepoResponse:
    repo = store.repos.get(payload.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="repo_id not found")
    try:
        result = index_repository(payload.repo_id, repo["path"])
        return IndexRepoResponse(
            status="completed",
            chunks=int(result.get("chunks", 0)),
            graph_url=result.get("graph_url"),
            stats=result.get("stats", {}),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@app.post("/chat", response_model=ChatResponse)
def chat_route(payload: ChatRequest) -> ChatResponse:
    conversation_id = payload.conversation_id or create_conversation(payload.project_id)
    add_message(conversation_id, "user", payload.message)

    store_ref = ChromaStore(collection=f"repo:{payload.project_id}")
    query_vec = embed([payload.message])
    results = store_ref.query(query_embeddings=query_vec, n_results=4)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    sources = []
    for idx, doc in enumerate(docs):
        meta = metas[idx] if idx < len(metas) else {}
        dist = distances[idx] if idx < len(distances) else None
        sources.append({
            "path": meta.get("path"),
            "chunk": meta.get("chunk"),
            "score": None if dist is None else float(dist),
            "excerpt": doc[:400],
        })

    context = "\n\n".join(docs)
    messages = [
        {"role": "system", "content": "You are a local self-hosted codebase agent. Cite sources from context."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {payload.message}"},
    ]
    answer = chat(messages)
    add_message(conversation_id, "assistant", answer)
    return ChatResponse(conversation_id=conversation_id, answer=answer, sources=sources)


@app.get("/chat/conversations", response_model=ConversationListResponse)
def chat_conversations(project_id: str) -> ConversationListResponse:
    return ConversationListResponse(conversations=[*list_conversations(project_id)])


@app.get("/chat/history", response_model=MessageHistoryResponse)
def chat_history(conversation_id: int) -> MessageHistoryResponse:
    return MessageHistoryResponse(messages=[*list_messages(conversation_id)])


@app.post("/feedback", response_model=FeedbackResponse)
def feedback_route(payload: FeedbackRequest) -> FeedbackResponse:
    add_feedback(payload.project_id, payload.run_id, payload.rating, payload.reason)
    return FeedbackResponse()


@app.post("/tasks/enqueue", response_model=TaskEnqueueResponse)
def enqueue_task_route(payload: TaskEnqueueRequest) -> TaskEnqueueResponse:
    task_id = enqueue_task(payload.project_id, payload.type, payload.payload)
    return TaskEnqueueResponse(task_id=task_id)


@app.get("/tasks/next", response_model=TaskStatusResponse)
def next_task_route() -> TaskStatusResponse:
    task = next_task()
    if not task:
        raise HTTPException(status_code=404, detail="no queued tasks")
    return TaskStatusResponse(task_id=task["id"], status="running", result=task)


@app.post("/tasks/complete", response_model=TaskStatusResponse)
def complete_task_route(payload: dict) -> TaskStatusResponse:
    task_id = int(payload.get("task_id", 0))
    status = payload.get("status", "completed")
    result = payload.get("result", {})
    if task_id <= 0:
        raise HTTPException(status_code=400, detail="task_id required")
    complete_task(task_id, status, result)
    return TaskStatusResponse(task_id=task_id, status=status, result=result)
