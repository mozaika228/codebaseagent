from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("CODEBASE_AGENT_DATA_DIR", BASE_DIR / ".data"))
REPOS_DIR = DATA_DIR / "repos"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
LOG_DIR = DATA_DIR / "logs"
BACKUP_DIR = DATA_DIR / "backups"
DB_PATH = Path(os.getenv("CODEBASE_AGENT_DB_PATH", DATA_DIR / "agent.sqlite3"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:70b")
OLLAMA_CODE_MODEL = os.getenv("OLLAMA_CODE_MODEL", "deepseek-coder-v2:32b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_FALLBACK_MODEL = os.getenv("OLLAMA_FALLBACK_MODEL", "qwen2.5:72b")

VECTOR_STORE = os.getenv("VECTOR_STORE", "chroma")
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", DATA_DIR / "vectorstore"))

REPOS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
