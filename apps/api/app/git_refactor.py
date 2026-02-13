from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path


class GitRefactorError(RuntimeError):
    pass


def _run_git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GitRefactorError(proc.stderr.strip() or proc.stdout.strip() or "git command failed")
    return proc.stdout.strip()


def create_refactor_commit(
    repo_path: str,
    base_branch: str,
    head_branch: str,
    proposal_id: str,
    files: list[str],
) -> dict[str, str]:
    repo_dir = Path(repo_path)

    if _has_remote(repo_dir, "origin"):
        _run_git(["fetch", "origin", base_branch], cwd=repo_dir)
        _run_git(["checkout", "-B", head_branch, f"origin/{base_branch}"], cwd=repo_dir)
    else:
        _run_git(["checkout", "-B", head_branch, base_branch], cwd=repo_dir)

    notes_dir = repo_dir / ".codebase-agent"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_file = notes_dir / f"{proposal_id}.md"
    timestamp = datetime.now(UTC).isoformat()
    body = [
        f"# Refactor Proposal {proposal_id}",
        "",
        f"Generated at: {timestamp}",
        "",
        "Target files:",
        *[f"- {path}" for path in files],
    ]
    note_file.write_text("\n".join(body) + "\n", encoding="utf-8")

    _run_git(["add", str(note_file.relative_to(repo_dir))], cwd=repo_dir)
    _run_git(["-c", "user.name=codebase-agent", "-c", "user.email=bot@codebase-agent.local", "commit", "-m", f"chore: apply {proposal_id} draft"], cwd=repo_dir)
    commit_sha = _run_git(["rev-parse", "HEAD"], cwd=repo_dir)
    return {"commit_sha": commit_sha, "head_branch": head_branch}


def _has_remote(repo_dir: Path, remote_name: str) -> bool:
    proc = subprocess.run(
        ["git", "remote", "get-url", remote_name],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0
