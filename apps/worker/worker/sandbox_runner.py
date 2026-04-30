from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxConfig:
  image_python: str = os.getenv("SANDBOX_IMAGE_PYTHON", "python:3.12-slim")
  image_node: str = os.getenv("SANDBOX_IMAGE_NODE", "node:20-bookworm-slim")
  timeout_seconds: int = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "900"))
  cpu_limit: str = os.getenv("SANDBOX_CPU_LIMIT", "1.5")
  memory_limit: str = os.getenv("SANDBOX_MEMORY_LIMIT", "2g")
  pids_limit: str = os.getenv("SANDBOX_PIDS_LIMIT", "256")
  network_mode: str = os.getenv("SANDBOX_NETWORK_MODE", "none")


def _detect_stack(repo_path: Path) -> str:
  if (repo_path / "package.json").exists():
    return "node"
  if (repo_path / "pyproject.toml").exists() or (repo_path / "pytest.ini").exists() or (repo_path / "requirements.txt").exists():
    return "python"
  return "unknown"


def _python_test_script(repo_path: Path) -> str:
  if (repo_path / "requirements-lock.txt").exists():
    install = "pip install --no-cache-dir -r requirements-lock.txt"
  elif (repo_path / "requirements.txt").exists():
    install = "pip install --no-cache-dir -r requirements.txt"
  else:
    install = "python -m pip install --no-cache-dir pytest"
  return f"set -e; {install}; pytest -q --maxfail=1"


def _node_test_script(repo_path: Path) -> str:
  if (repo_path / "package-lock.json").exists() or (repo_path / "npm-shrinkwrap.json").exists():
    install = "npm ci"
  else:
    install = "npm install"
  return f"set -e; {install}; npm test"


def _docker_cmd(repo_path: Path, image: str, shell_script: str, cfg: SandboxConfig) -> list[str]:
  return [
    "docker", "run", "--rm",
    "--network", cfg.network_mode,
    "--cpus", cfg.cpu_limit,
    "--memory", cfg.memory_limit,
    "--pids-limit", cfg.pids_limit,
    "--read-only",
    "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m",
    "-e", "PYTHONHASHSEED=0",
    "-e", "TZ=UTC",
    "-e", "LC_ALL=C.UTF-8",
    "-v", f"{str(repo_path)}:/workspace:rw",
    "-w", "/workspace",
    image,
    "sh", "-lc", shell_script,
  ]


def run_tests_in_sandbox(repo_path: str) -> dict[str, str | bool]:
  root = Path(repo_path)
  stack = _detect_stack(root)
  if stack == "unknown":
    return {"status": "skipped", "summary": "no test runner detected", "sandbox": True, "deterministic": True}

  cfg = SandboxConfig()
  if stack == "python":
    image = cfg.image_python
    script = _python_test_script(root)
  else:
    image = cfg.image_node
    script = _node_test_script(root)

  cmd = _docker_cmd(root, image, script, cfg)
  try:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=cfg.timeout_seconds, check=False)
  except subprocess.TimeoutExpired:
    return {
      "status": "failed",
      "summary": "sandbox timeout",
      "sandbox": True,
      "deterministic": True,
      "cmd": " ".join(shlex.quote(item) for item in cmd),
    }

  summary = (proc.stdout + "\n" + proc.stderr).strip()[-4000:]
  return {
    "status": "passed" if proc.returncode == 0 else "failed",
    "summary": summary,
    "sandbox": True,
    "deterministic": True,
    "cmd": " ".join(shlex.quote(item) for item in cmd),
  }
