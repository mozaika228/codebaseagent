from __future__ import annotations

import json
from pathlib import Path

from app.ast_analyzer import analyze_repository
from app.config import ARTIFACTS_DIR


def test_analyze_repository_creates_graph_and_hotspots(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    (repo / "mod.py").write_text(
        "import math\n\n\ndef calc(x):\n    if x > 1 and x < 10:\n        return math.ceil(x)\n    return x\n",
        encoding="utf-8",
    )
    (repo / "ui.ts").write_text("export const id = 1;\n", encoding="utf-8")

    analysis_id = "a_test_ast"
    result = analyze_repository(str(repo), analysis_id)
    assert result["status"] == "completed"
    assert "hotspots" in result
    assert result["module_graph_url"] == f"/artifacts/{analysis_id}/graph.json"

    graph_path = ARTIFACTS_DIR / analysis_id / "graph.json"
    assert graph_path.exists()
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    assert isinstance(payload["nodes"], list)
    assert isinstance(payload["edges"], list)
