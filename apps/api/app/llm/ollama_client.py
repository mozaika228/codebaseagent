from __future__ import annotations

import time
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import (
  OLLAMA_BASE_URL,
  OLLAMA_CHAT_MODEL,
  OLLAMA_CODE_MODEL,
  OLLAMA_EMBED_MODEL,
  OLLAMA_FALLBACK_MODEL,
)


class OllamaError(RuntimeError):
  pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
  url = f"{OLLAMA_BASE_URL}{path}"
  resp = requests.post(url, json=payload, timeout=60)
  if resp.status_code >= 400:
    raise OllamaError(f"Ollama error {resp.status_code}: {resp.text}")
  return resp.json()


def chat(messages: list[dict[str, str]], model: str | None = None) -> str:
  selected = model or OLLAMA_CHAT_MODEL
  try:
    data = _post("/api/chat", {"model": selected, "messages": messages, "stream": False})
  except Exception:
    if OLLAMA_FALLBACK_MODEL and selected != OLLAMA_FALLBACK_MODEL:
      data = _post("/api/chat", {"model": OLLAMA_FALLBACK_MODEL, "messages": messages, "stream": False})
    else:
      raise
  return data.get("message", {}).get("content", "")


def code(messages: list[dict[str, str]]) -> str:
  return chat(messages, model=OLLAMA_CODE_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
  vectors: list[list[float]] = []
  for text in texts:
    if not text.strip():
      vectors.append([])
      continue
    data = _post("/api/embeddings", {"model": OLLAMA_EMBED_MODEL, "prompt": text})
    vectors.append(data.get("embedding", []))
    time.sleep(0.01)
  return vectors
