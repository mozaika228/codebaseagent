from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..llm.ollama_client import embed
from ..vector_store.chroma_store import ChromaStore
from .graph_index import build_graph


def _iter_code_files(repo_path: Path) -> list[Path]:
  ignore_dirs = {".git", "node_modules", ".next", ".venv", "venv", "__pycache__"}
  files: list[Path] = []
  for path in repo_path.rglob("*"):
    if any(part in ignore_dirs for part in path.parts):
      continue
    if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java"}:
      files.append(path)
  return files


def _chunk_lines(text: str, max_lines: int = 200) -> Iterable[str]:
  lines = text.splitlines()
  for i in range(0, len(lines), max_lines):
    yield "\n".join(lines[i : i + max_lines])


def index_repository(repo_id: str, repo_path: str) -> dict[str, object]:
  root = Path(repo_path)
  store = ChromaStore(collection=f"repo:{repo_id}")
  ids: list[str] = []
  embeddings: list[list[float]] = []
  metadatas: list[dict[str, str]] = []
  documents: list[str] = []

  for file_path in _iter_code_files(root):
    rel = file_path.relative_to(root).as_posix()
    try:
      content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
      continue
    for chunk_idx, chunk in enumerate(_chunk_lines(content)):
      if not chunk.strip():
        continue
      ids.append(f"{rel}:{chunk_idx}")
      documents.append(chunk)
      metadatas.append({"path": rel, "chunk": str(chunk_idx)})
  if documents:
    embeddings = embed(documents)
    store.add_documents(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

  graph_meta = build_graph(repo_path, repo_id)
  return {"chunks": len(ids), **graph_meta}
