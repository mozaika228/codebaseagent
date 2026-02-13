from __future__ import annotations

import ast
import json
from collections import Counter, defaultdict
from pathlib import Path

from .config import ARTIFACTS_DIR

try:
    from tree_sitter_languages import get_parser
except ImportError:  # pragma: no cover - optional at runtime
    get_parser = None


class _PyFileVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.function_count = 0
        self.class_count = 0
        self.imports: list[str] = []
        self.calls: list[str] = []
        self.complexity = 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_count += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_count += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_count += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node)
        if name:
            self.calls.append(name)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.complexity += len(node.handlers) or 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.complexity += max(1, len(node.values) - 1)
        self.generic_visit(node)


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _iter_code_files(repo_path: Path) -> list[Path]:
    ignore_dirs = {".git", "node_modules", ".next", ".venv", "venv", "__pycache__"}
    files: list[Path] = []
    for path in repo_path.rglob("*"):
        if any(part in ignore_dirs for part in path.parts):
            continue
        if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            files.append(path)
    return files


def _iter_ts_nodes(root) -> list:
    stack = [root]
    out = []
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(reversed(node.children))
    return out


def _analyze_ts_js(file_path: Path, parser, call_counter: Counter[str]) -> tuple[list[str], int]:
    source = file_path.read_bytes()
    tree = parser.parse(source)
    imports: list[str] = []
    complexity = 1
    interesting_types = {
        "if_statement",
        "for_statement",
        "for_in_statement",
        "while_statement",
        "switch_case",
        "catch_clause",
        "ternary_expression",
        "logical_expression",
    }
    call_like = {"call_expression", "new_expression"}

    for node in _iter_ts_nodes(tree.root_node):
        node_type = node.type
        if node_type in {"import_statement", "import_clause", "export_statement"}:
            snippet = source[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")
            imports.append(snippet.strip())
        if node_type in interesting_types:
            complexity += 1
        if node_type in call_like:
            call_counter.update([node_type])

    return imports, complexity


def analyze_repository(repo_path: str, analysis_id: str) -> dict[str, object]:
    repo_root = Path(repo_path)
    code_files = _iter_code_files(repo_root)

    py_nodes = 0
    ts_nodes = 0
    dependency_edges: dict[str, set[str]] = defaultdict(set)
    file_scores: list[tuple[str, int]] = []
    call_counter: Counter[str] = Counter()
    js_parser = get_parser("javascript") if get_parser else None
    ts_parser = get_parser("typescript") if get_parser else None

    for file_path in code_files:
        rel = file_path.relative_to(repo_root).as_posix()
        if file_path.suffix == ".py":
            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                file_scores.append((rel, 1))
                continue

            visitor = _PyFileVisitor()
            visitor.visit(tree)
            py_nodes += 1
            for dep in visitor.imports:
                dependency_edges[rel].add(dep)
            call_counter.update(visitor.calls)
            score = visitor.complexity + visitor.function_count + visitor.class_count
            file_scores.append((rel, score))
            continue

        if file_path.suffix in {".js", ".jsx"} and js_parser:
            try:
                imports, complexity = _analyze_ts_js(file_path, js_parser, call_counter)
            except UnicodeDecodeError:
                file_scores.append((rel, 1))
                continue
            ts_nodes += 1
            for dep in imports:
                dependency_edges[rel].add(dep)
            file_scores.append((rel, complexity))
            continue

        if file_path.suffix in {".ts", ".tsx"} and ts_parser:
            try:
                imports, complexity = _analyze_ts_js(file_path, ts_parser, call_counter)
            except UnicodeDecodeError:
                file_scores.append((rel, 1))
                continue
            ts_nodes += 1
            for dep in imports:
                dependency_edges[rel].add(dep)
            file_scores.append((rel, complexity))
            continue

        file_scores.append((rel, 1))

    hotspots = [
        {"file": file_name, "reason": f"high structural complexity score={score}"}
        for file_name, score in sorted(file_scores, key=lambda item: item[1], reverse=True)[:5]
    ]

    top_calls = ", ".join(name for name, _ in call_counter.most_common(5)) or "n/a"
    summary = (
        f"Scanned {len(code_files)} code files; parsed {py_nodes} Python and {ts_nodes} JS/TS files via AST. "
        f"Top recurring calls: {top_calls}."
    )

    graph_payload = {
        "nodes": sorted({*dependency_edges.keys()}),
        "edges": [
            {"from": src, "to": dep}
            for src, deps in dependency_edges.items()
            for dep in sorted(deps)
        ],
    }

    graph_dir = ARTIFACTS_DIR / analysis_id
    graph_dir.mkdir(parents=True, exist_ok=True)
    graph_path = graph_dir / "graph.json"
    graph_path.write_text(json.dumps(graph_payload, indent=2), encoding="utf-8")

    return {
        "status": "completed",
        "summary": summary,
        "hotspots": hotspots,
        "module_graph_url": f"/artifacts/{analysis_id}/graph.json",
    }
