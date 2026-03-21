from __future__ import annotations

from app.llm import ollama_client


def test_ollama_chat_and_embed(monkeypatch) -> None:
  calls = []

  def fake_post(path, payload):
    calls.append((path, payload))
    if path == "/api/chat":
      return {"message": {"content": "ok"}}
    if path == "/api/embeddings":
      return {"embedding": [0.1, 0.2]}
    return {}

  monkeypatch.setattr(ollama_client, "_post", fake_post)
  out = ollama_client.chat([{"role": "user", "content": "hi"}], model="test")
  assert out == "ok"
  vecs = ollama_client.embed(["hello"])
  assert vecs == [[0.1, 0.2]]
  assert calls
