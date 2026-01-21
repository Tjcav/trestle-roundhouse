import ast
from pathlib import Path


def _class_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def test_single_node_schema() -> None:
    matches: list[Path] = []
    for py in Path(".").rglob("*.py"):
        if py.parts[0] in {".venv", "node_modules", ".git"}:
            continue
        names = _class_names(py)
        if "NodeType" in names or "NodeResponse" in names:
            matches.append(py)
    assert matches == [Path("core/nodes/models.py")], f"Multiple Node schemas found: {matches}"
