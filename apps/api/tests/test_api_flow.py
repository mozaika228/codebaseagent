from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import ARTIFACTS_DIR


def _run_git(args: list[str], cwd: Path) -> None:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)


def _init_repo(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    (path / "service.py").write_text(
        "import os\n\n\ndef run(flag: bool) -> int:\n    if flag:\n        return 1\n    return 0\n",
        encoding="utf-8",
    )
    _run_git(["init"], path)
    _run_git(["checkout", "-b", "main"], path)
    _run_git(["add", "."], path)
    _run_git(
        [
            "-c",
            "user.name=tests",
            "-c",
            "user.email=tests@example.local",
            "commit",
            "-m",
            "init",
        ],
        path,
    )
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(path), capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def test_end_to_end_flow_with_local_pr_draft(client: TestClient, monkeypatch, tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    commit_sha = _init_repo(repo_path)

    def fake_ingest(repo_url: str, branch: str) -> dict[str, str]:
        assert repo_url.startswith("https://")
        assert branch == "main"
        return {"path": str(repo_path), "commit_sha": commit_sha}

    monkeypatch.setattr("app.main.ingest_repository", fake_ingest)

    import_res = client.post("/repos/import", json={"repo_url": "https://github.com/acme/demo", "branch": "main"})
    assert import_res.status_code == 200
    repo_id = import_res.json()["repo_id"]

    analysis_res = client.post("/analysis/run", json={"repo_id": repo_id, "commit_sha": "HEAD"})
    assert analysis_res.status_code == 200
    analysis_id = analysis_res.json()["analysis_id"]

    detail_res = client.get(f"/analysis/{analysis_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == "completed"

    proposal_res = client.post(
        "/refactors/propose",
        json={"analysis_id": analysis_id, "scope": ["src/**"], "max_changes": 5},
    )
    assert proposal_res.status_code == 200
    proposal_id = proposal_res.json()["proposal_id"]

    apply_res = client.post("/refactors/apply", json={"proposal_id": proposal_id, "run_tests": True})
    assert apply_res.status_code == 200
    run_id = apply_res.json()["run_id"]

    pr_res = client.post(
        "/github/pr",
        json={
            "run_id": run_id,
            "repo_id": repo_id,
            "base": "main",
            "head_branch": f"codebase-agent/{proposal_id}",
            "title": "AI agent: refactor proposal",
            "body": "Generated in tests",
        },
    )
    assert pr_res.status_code == 200
    assert pr_res.json()["status"] == "skipped"
    assert pr_res.json()["pr_url"] == f"/artifacts/pr-drafts/{run_id}.md"

    draft_path = ARTIFACTS_DIR / "pr-drafts" / f"{run_id}.md"
    assert draft_path.exists()
