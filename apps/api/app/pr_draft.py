from __future__ import annotations

from pathlib import Path

from .config import ARTIFACTS_DIR


def write_local_pr_draft(
    run_id: str,
    repo_url: str,
    base: str,
    head_branch: str,
    title: str,
    body: str,
    commit_sha: str,
) -> str:
    drafts_dir = ARTIFACTS_DIR / "pr-drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    draft_path = drafts_dir / f"{run_id}.md"
    content = [
        f"# {title}",
        "",
        body,
        "",
        "## Metadata",
        f"- repo: {repo_url}",
        f"- base: {base}",
        f"- head: {head_branch}",
        f"- commit: {commit_sha}",
        "",
        "## Status",
        "GitHub App credentials are missing; draft PR was generated locally.",
    ]
    draft_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return f"/artifacts/pr-drafts/{run_id}.md"
