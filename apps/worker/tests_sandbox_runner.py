from __future__ import annotations

from pathlib import Path

from worker.sandbox_runner import SandboxConfig, _docker_cmd


def test_docker_cmd_has_isolation_flags(tmp_path: Path) -> None:
  cfg = SandboxConfig(cpu_limit="1.0", memory_limit="1g", pids_limit="128", network_mode="none")
  repo = tmp_path / "repo"
  repo.mkdir(parents=True)
  cmd = _docker_cmd(repo, "python:3.12-slim", "pytest -q", cfg)

  joined = " ".join(cmd)
  assert "--network none" in joined
  assert "--cpus 1.0" in joined
  assert "--memory 1g" in joined
  assert "--pids-limit 128" in joined
  assert "--read-only" in joined
  assert "PYTHONHASHSEED=0" in joined
