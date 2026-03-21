from __future__ import annotations

import importlib
import os
from pathlib import Path


def test_sqlite_memory_roundtrip(tmp_path: Path) -> None:
  db_path = tmp_path / "agent.sqlite3"
  os.environ["CODEBASE_AGENT_DB_PATH"] = str(db_path)
  from app.memory import sqlite_memory
  importlib.reload(sqlite_memory)

  sqlite_memory.init_db()
  conv_id = sqlite_memory.create_conversation("p1")
  sqlite_memory.add_message(conv_id, "user", "hello")
  sqlite_memory.add_message(conv_id, "assistant", "world")

  conversations = sqlite_memory.list_conversations("p1")
  assert conversations[0]["id"] == conv_id

  messages = sqlite_memory.list_messages(conv_id)
  assert len(messages) == 2
  assert messages[0]["role"] == "user"
