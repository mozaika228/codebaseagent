from __future__ import annotations

import os

from app import github_app


def test_github_parse_and_auth_url(monkeypatch) -> None:
  owner, repo = github_app.parse_github_repo_url("https://github.com/acme/demo.git")
  assert owner == "acme"
  assert repo == "demo"

  url = github_app._authenticated_remote_url("https://github.com/acme/demo", "token")
  assert url.startswith("https://x-access-token:token@")

  monkeypatch.delenv("GITHUB_APP_ID", raising=False)
  monkeypatch.delenv("GITHUB_APP_INSTALLATION_ID", raising=False)
  monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
  assert github_app.is_github_app_configured() is False
