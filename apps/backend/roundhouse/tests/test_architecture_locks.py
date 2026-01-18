from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HA_DIR = ROOT / "ha"
TRESTLE_DIR = ROOT / "trestle_bridge"


def _py_files(base: Path) -> list[Path]:
    return [p for p in base.rglob("*.py") if p.is_file()]


def _imports_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module)
    return mods


def test_ha_does_not_import_trestle_bridge() -> None:
    forbidden_prefixes = ("roundhouse.trestle_bridge", "trestle_bridge")
    for file_path in _py_files(HA_DIR):
        imports = _imports_in_file(file_path)
        bad = [m for m in imports if m.startswith(forbidden_prefixes)]
        assert not bad, f"{file_path} imports forbidden modules: {bad}"


def test_trestle_bridge_does_not_import_ha() -> None:
    forbidden_prefixes = ("roundhouse.ha", "ha")
    for file_path in _py_files(TRESTLE_DIR):
        imports = _imports_in_file(file_path)
        bad = [m for m in imports if m.startswith(forbidden_prefixes)]
        assert not bad, f"{file_path} imports forbidden modules: {bad}"
