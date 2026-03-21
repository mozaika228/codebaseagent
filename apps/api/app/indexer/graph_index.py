from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from ..config import ARTIFACTS_DIR

IMPORT_PATTERNS = {
  ".py": [
    re.compile(r"^\s*import\s+([\w\.]+)", re.MULTILINE),
    re.compile(r"^\s*from\s+([\w\.]+)\s+import", re.MULTILINE),
  ],
  ".js": [
    re.compile(r"import\s+.*?from\s+[\"']([^\"']+)[\"']"),
    re.compile(r"require\([\"']([^\"']+)[\"']\)"),
  ],
  ".jsx": [
    re.compile(r"import\s+.*?from\s+[\"']([^\"']+)[\"']"),
    re.compile(r"require\([\"']([^\"']+)[\"']\)"),
  ],
  ".ts": [
    re.compile(r"import\s+.*?from\s+[\"']([^\"']+)[\"']"),
    re.compile(r"require\([\"']([^\"']+)[\"']\)"),
  ],
  ".tsx": [
    re.compile(r"import\s+.*?from\s+[\"']([^\"']+)[\"']"),
    re.compile(r"require\([\"']([^\"']+)[\"']\)"),
  ],
  ".go": [
    re.compile(r"import\s+\(.*?\)", re.DOTALL),
    re.compile(r"import\s+\"([^\"]+)\""),
  ],
  ".rs": [
    re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE),
  ],
  ".java": [
    re.compile(r"^\s*import\s+([\w\.]+);", re.MULTILINE),
  ],
}

LANG_BY_EXT = {
  ".py": "python",
  ".js": "javascript",
  ".jsx": "javascript",
  ".ts": "typescript",
  ".tsx": "typescript",
  ".go": "go",
  ".rs": "rust",
  ".java": "java",
}


def _iter_code_files(repo_path: Path) -> Iterable[Path]:
  ignore_dirs = {".git", "node_modules", ".next", ".venv", "venv", "__pycache__"}
  for path in repo_path.rglob("*"):
    if any(part in ignore_dirs for part in path.parts):
      continue
    if path.is_file() and path.suffix in LANG_BY_EXT:
      yield path


def _extract_imports(ext: str, text: str) -> list[str]:
  patterns = IMPORT_PATTERNS.get(ext, [])
  imports: list[str] = []
  for pattern in patterns:
    if ext == ".go" and pattern.pattern.startswith("import\\s+\\("):
      for block in pattern.findall(text):
        imports.extend(re.findall(r"\"([^\"]+)\"", block))
      continue
    imports.extend(pattern.findall(text))
  return [imp.strip() for imp in imports if imp.strip()]


def _tag_path(path: str) -> list[str]:
  tags: list[str] = []
  lower = path.lower()
  if "test" in lower or "spec" in lower:
    tags.append("test")
  if "api" in lower:
    tags.append("api")
  if "service" in lower:
    tags.append("service")
  if "controller" in lower or "handler" in lower:
    tags.append("controller")
  if "db" in lower or "repo" in lower:
    tags.append("data")
  return tags


def build_graph(repo_path: str, repo_id: str) -> dict[str, object]:
  root = Path(repo_path)
  edges: list[dict[str, str]] = []
  nodes: set[str] = set()
  lang_counts: Counter[str] = Counter()
  tag_counts: Counter[str] = Counter()

  for file_path in _iter_code_files(root):
    rel = file_path.relative_to(root).as_posix()
    nodes.add(rel)
    lang = LANG_BY_EXT.get(file_path.suffix, "unknown")
    lang_counts[lang] += 1
    for tag in _tag_path(rel):
      tag_counts[tag] += 1
    try:
      text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
      continue
    for imp in _extract_imports(file_path.suffix, text):
      edges.append({"from": rel, "to": imp, "type": "import"})

  graph = {
    "nodes": sorted(nodes),
    "edges": edges,
    "stats": {
      "languages": dict(lang_counts),
      "tags": dict(tag_counts),
      "edge_count": len(edges),
      "node_count": len(nodes),
    },
  }

  graph_dir = ARTIFACTS_DIR / "index" / repo_id
  graph_dir.mkdir(parents=True, exist_ok=True)
  graph_path = graph_dir / "graph.json"
  graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
  return {
    "graph_url": f"/artifacts/index/{repo_id}/graph.json",
    "stats": graph["stats"],
  }
