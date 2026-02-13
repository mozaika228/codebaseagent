from __future__ import annotations

from pathlib import Path

from app.config import ARTIFACTS_DIR
from app.pr_draft import write_local_pr_draft


def test_write_local_pr_draft_persists_file() -> None:
    run_id = "run_test_local_draft"
    url = write_local_pr_draft(
        run_id=run_id,
        repo_url="https://github.com/acme/project",
        base="main",
        head_branch="codebase-agent/p_test",
        title="Demo title",
        body="Demo body",
        commit_sha="abc123",
    )
    assert url == f"/artifacts/pr-drafts/{run_id}.md"

    draft_path = ARTIFACTS_DIR / "pr-drafts" / f"{run_id}.md"
    assert draft_path.exists()
    text = draft_path.read_text(encoding="utf-8")
    assert "Demo title" in text
    assert "codebase-agent/p_test" in text
