from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any

import requests

DB_PATH = "../.data/agent.sqlite3"
API_BASE = "http://localhost:8000"


@dataclass
class Task:
  id: int
  project_id: str
  type: str
  payload: dict[str, Any]


def _conn() -> sqlite3.Connection:
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn


def next_task() -> Task | None:
  conn = _conn()
  cur = conn.cursor()
  row = cur.execute(
    "SELECT id, project_id, type, payload_json FROM tasks WHERE status='queued' ORDER BY id ASC LIMIT 1"
  ).fetchone()
  if not row:
    conn.close()
    return None
  cur.execute("UPDATE tasks SET status='running' WHERE id=?", (row["id"],))
  conn.commit()
  conn.close()
  return Task(id=row["id"], project_id=row["project_id"], type=row["type"], payload=json.loads(row["payload_json"]))


def complete_task(task_id: int, status: str, result: dict[str, Any] | None = None) -> None:
  conn = _conn()
  cur = conn.cursor()
  cur.execute(
    "UPDATE tasks SET status=?, result_json=? WHERE id=?",
    (status, json.dumps(result or {}), task_id),
  )
  conn.commit()
  conn.close()


def run_task(task: Task) -> dict[str, Any]:
  if task.type == "index_repo":
    resp = requests.post(f"{API_BASE}/index/repo", json={"repo_id": task.project_id}, timeout=300)
    return {"status_code": resp.status_code, "body": resp.text}
  return {"status": "unknown task"}


def main() -> None:
  while True:
    task = next_task()
    if not task:
      time.sleep(2)
      continue
    try:
      result = run_task(task)
      complete_task(task.id, "completed", result)
    except Exception as exc:
      complete_task(task.id, "failed", {"error": str(exc)})


if __name__ == "__main__":
  main()
