from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from .config import BASE_DIR, REPOS_DIR


class RepoIngestError(RuntimeError):
    pass


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RepoIngestError(proc.stderr.strip() or proc.stdout.strip() or "git command failed")
    return proc.stdout.strip()


def _repo_dir_name(repo_url: str) -> str:
    return hashlib.sha256(repo_url.encode("utf-8")).hexdigest()[:16]


def install_post_commit_hook(repo_path: str, repo_id: str) -> None:
    repo_dir = Path(repo_path)
    hooks_dir = repo_dir / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "post-commit"
    worker_path = BASE_DIR / "apps" / "worker"
    hook = "\n".join(
        [
            "#!/usr/bin/env sh",
            f"PYTHONPATH=\"{worker_path.as_posix()}\" python -m worker.index_repo --repo-id {repo_id} --api http://localhost:8000",
            "exit 0",
            "",
        ]
    )
    hook_path.write_text(hook, encoding="utf-8")


def ingest_repository(repo_url: str, branch: str) -> dict[str, str]:
    repo_dir = REPOS_DIR / _repo_dir_name(repo_url)
    if not repo_dir.exists():
        _run_git(["clone", "--depth", "1", "--branch", branch, repo_url, str(repo_dir)])
    else:
        _run_git(["fetch", "origin", branch, "--depth", "1"], cwd=repo_dir)
        _run_git(["checkout", branch], cwd=repo_dir)
        _run_git(["reset", "--hard", f"origin/{branch}"], cwd=repo_dir)

    commit_sha = _run_git(["rev-parse", "HEAD"], cwd=repo_dir)
    return {"path": str(repo_dir), "commit_sha": commit_sha}
