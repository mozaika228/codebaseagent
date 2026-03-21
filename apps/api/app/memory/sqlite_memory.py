from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from ..config import DB_PATH


def _conn() -> sqlite3.Connection:
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn


def init_db() -> None:
  conn = _conn()
  cur = conn.cursor()
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS conversations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
    """
  )
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id INTEGER NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(conversation_id) REFERENCES conversations(id)
    )
    """
  )
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS feedback (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id TEXT NOT NULL,
      run_id TEXT,
      rating TEXT NOT NULL,
      reason TEXT,
      created_at TEXT NOT NULL
    )
    """
  )
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id TEXT NOT NULL,
      type TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      status TEXT NOT NULL,
      result_json TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
    """
  )
  conn.commit()
  conn.close()


def _now() -> str:
  return datetime.now(UTC).isoformat()


def create_conversation(project_id: str) -> int:
  conn = _conn()
  cur = conn.cursor()
  now = _now()
  cur.execute(
    "INSERT INTO conversations (project_id, created_at, updated_at) VALUES (?, ?, ?)",
    (project_id, now, now),
  )
  conn.commit()
  conv_id = int(cur.lastrowid)
  conn.close()
  return conv_id


def list_conversations(project_id: str) -> list[dict[str, Any]]:
  conn = _conn()
  cur = conn.cursor()
  rows = cur.execute(
    "SELECT id, created_at, updated_at FROM conversations WHERE project_id=? ORDER BY updated_at DESC",
    (project_id,),
  ).fetchall()
  conn.close()
  return [dict(row) for row in rows]


def add_message(conversation_id: int, role: str, content: str) -> None:
  conn = _conn()
  cur = conn.cursor()
  cur.execute(
    "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
    (conversation_id, role, content, _now()),
  )
  cur.execute(
    "UPDATE conversations SET updated_at=? WHERE id=?",
    (_now(), conversation_id),
  )
  conn.commit()
  conn.close()


def list_messages(conversation_id: int) -> list[dict[str, Any]]:
  conn = _conn()
  cur = conn.cursor()
  rows = cur.execute(
    "SELECT role, content, created_at FROM messages WHERE conversation_id=? ORDER BY id ASC",
    (conversation_id,),
  ).fetchall()
  conn.close()
  return [dict(row) for row in rows]


def add_feedback(project_id: str, run_id: str | None, rating: str, reason: str | None) -> None:
  conn = _conn()
  cur = conn.cursor()
  cur.execute(
    "INSERT INTO feedback (project_id, run_id, rating, reason, created_at) VALUES (?, ?, ?, ?, ?)",
    (project_id, run_id, rating, reason, _now()),
  )
  conn.commit()
  conn.close()


def enqueue_task(project_id: str, task_type: str, payload: dict[str, Any]) -> int:
  conn = _conn()
  cur = conn.cursor()
  now = _now()
  cur.execute(
    "INSERT INTO tasks (project_id, type, payload_json, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
    (project_id, task_type, json.dumps(payload), "queued", now, now),
  )
  conn.commit()
  task_id = int(cur.lastrowid)
  conn.close()
  return task_id


def next_task() -> dict[str, Any] | None:
  conn = _conn()
  cur = conn.cursor()
  row = cur.execute(
    "SELECT id, project_id, type, payload_json FROM tasks WHERE status='queued' ORDER BY id ASC LIMIT 1"
  ).fetchone()
  if not row:
    conn.close()
    return None
  cur.execute("UPDATE tasks SET status='running', updated_at=? WHERE id=?", (_now(), row["id"]))
  conn.commit()
  conn.close()
  return {"id": row["id"], "project_id": row["project_id"], "type": row["type"], "payload": json.loads(row["payload_json"]) }


def complete_task(task_id: int, status: str, result: dict[str, Any] | None = None) -> None:
  conn = _conn()
  cur = conn.cursor()
  cur.execute(
    "UPDATE tasks SET status=?, result_json=?, updated_at=? WHERE id=?",
    (status, json.dumps(result or {}), _now(), task_id),
  )
  conn.commit()
  conn.close()
