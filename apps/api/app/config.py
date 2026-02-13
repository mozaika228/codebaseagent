from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("CODEBASE_AGENT_DATA_DIR", BASE_DIR / ".data"))
REPOS_DIR = DATA_DIR / "repos"
ARTIFACTS_DIR = DATA_DIR / "artifacts"

REPOS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
