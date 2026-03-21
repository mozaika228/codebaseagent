from __future__ import annotations

from pathlib import Path

from app.indexer.graph_index import _extract_imports, build_graph


def test_extract_imports_python_and_js() -> None:
  py = "import os\nfrom sys import path\n"
  js = "import foo from 'bar'\nconst x = require('baz')\n"
  assert "os" in _extract_imports(".py", py)
  assert "sys" in _extract_imports(".py", py)
  assert "bar" in _extract_imports(".js", js)
  assert "baz" in _extract_imports(".js", js)


def test_build_graph_writes_artifact(tmp_path: Path) -> None:
  repo = tmp_path / "repo"
  repo.mkdir(parents=True)
  (repo / "main.py").write_text("import os\n", encoding="utf-8")
  (repo / "util.ts").write_text("import x from 'y'\n", encoding="utf-8")

  result = build_graph(str(repo), "r_test")
  assert result["graph_url"].endswith("/artifacts/index/r_test/graph.json")
  stats = result["stats"]
  assert stats["node_count"] == 2
  assert stats["edge_count"] >= 2
