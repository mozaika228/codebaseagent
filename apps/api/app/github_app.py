from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import jwt
import requests


class GithubAppError(RuntimeError):
    pass


def is_github_app_configured() -> bool:
    return bool(
        os.getenv("GITHUB_APP_ID", "").strip()
        and os.getenv("GITHUB_APP_INSTALLATION_ID", "").strip()
        and os.getenv("GITHUB_APP_PRIVATE_KEY", "").strip()
    )


@dataclass
class GithubAppConfig:
    app_id: str
    private_key: str
    installation_id: str
    api_url: str = "https://api.github.com"

    @classmethod
    def from_env(cls) -> "GithubAppConfig":
        app_id = os.getenv("GITHUB_APP_ID", "")
        private_key = os.getenv("GITHUB_APP_PRIVATE_KEY", "")
        installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID", "")
        if not app_id or not private_key or not installation_id:
            raise GithubAppError("GitHub App environment variables are not fully configured")
        private_key = private_key.replace("\\n", "\n")
        return cls(app_id=app_id, private_key=private_key, installation_id=installation_id)


def _build_app_jwt(config: GithubAppConfig) -> str:
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 9 * 60, "iss": config.app_id}
    return jwt.encode(payload, config.private_key, algorithm="RS256")


def _request_installation_token(config: GithubAppConfig) -> str:
    app_jwt = _build_app_jwt(config)
    url = f"{config.api_url}/app/installations/{config.installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.post(url, headers=headers, timeout=20)
    if resp.status_code >= 400:
        raise GithubAppError(f"Failed to create installation token: {resp.status_code} {resp.text}")
    return resp.json()["token"]


def get_installation_token_from_env() -> str:
    config = GithubAppConfig.from_env()
    return _request_installation_token(config)


def _api_request(
    method: str,
    url: str,
    token: str,
    payload: dict | None = None,
    allow_statuses: set[int] | None = None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.request(method, url, headers=headers, json=payload, timeout=20)
    if allow_statuses and resp.status_code in allow_statuses:
        return {"status_code": resp.status_code, "raw": resp.text}
    if resp.status_code >= 400:
        raise GithubAppError(f"GitHub API error: {resp.status_code} {resp.text}")
    if resp.text:
        return resp.json()
    return {}


def parse_github_repo_url(repo_url: str) -> tuple[str, str]:
    trimmed = repo_url.rstrip("/")
    if trimmed.endswith(".git"):
        trimmed = trimmed[:-4]
    parts = trimmed.split("/")
    if len(parts) < 2:
        raise GithubAppError("Invalid GitHub repository URL")
    owner = parts[-2]
    repo = parts[-1]
    return owner, repo


def create_pr(
    repo_url: str,
    base: str,
    head_branch: str,
    title: str,
    body: str,
) -> str:
    config = GithubAppConfig.from_env()
    token = _request_installation_token(config)
    owner, repo = parse_github_repo_url(repo_url)
    ensure_branch_exists(config.api_url, token, owner, repo, base, head_branch)
    url = f"{config.api_url}/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base,
        "draft": True,
    }
    data = _api_request("POST", url, token, payload)
    return data["html_url"]


def push_branch(repo_path: str, repo_url: str, head_branch: str, token: str) -> None:
    remote_url = _authenticated_remote_url(repo_url, token)
    repo_dir = Path(repo_path)
    _run_git_allow_fail(["remote", "remove", "codebase-agent-auth"], cwd=repo_dir)
    _run_git(["remote", "add", "codebase-agent-auth", remote_url], cwd=repo_dir)
    try:
        _run_git(["push", "-u", "codebase-agent-auth", head_branch], cwd=repo_dir)
    finally:
        _run_git_allow_fail(["remote", "remove", "codebase-agent-auth"], cwd=repo_dir)


def _authenticated_remote_url(repo_url: str, token: str) -> str:
    trimmed = repo_url.rstrip("/")
    if trimmed.endswith(".git"):
        trimmed = trimmed[:-4]
    if not trimmed.startswith("https://"):
        raise GithubAppError("Only https GitHub remotes are supported for authenticated push")
    return trimmed.replace("https://", f"https://x-access-token:{token}@", 1) + ".git"


def _run_git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GithubAppError(proc.stderr.strip() or proc.stdout.strip() or "git command failed")
    return proc.stdout.strip()


def _run_git_allow_fail(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def ensure_branch_exists(
    api_url: str,
    token: str,
    owner: str,
    repo: str,
    base: str,
    head_branch: str,
) -> None:
    head_ref_url = f"{api_url}/repos/{owner}/{repo}/git/ref/heads/{head_branch}"
    head_resp = _api_request("GET", head_ref_url, token, allow_statuses={404})
    if head_resp.get("status_code") != 404:
        return

    base_ref_url = f"{api_url}/repos/{owner}/{repo}/git/ref/heads/{base}"
    base_ref = _api_request("GET", base_ref_url, token)
    base_sha = base_ref["object"]["sha"]

    create_ref_url = f"{api_url}/repos/{owner}/{repo}/git/refs"
    _api_request(
        "POST",
        create_ref_url,
        token,
        payload={"ref": f"refs/heads/{head_branch}", "sha": base_sha},
        allow_statuses={422},
    )
