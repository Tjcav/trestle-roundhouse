from pathlib import Path

FORBIDDEN = {
    "core": ["apps", "simulator", "fastapi"],
    "libs/shared_py": ["apps"],
}


def test_no_forbidden_imports() -> None:
    for layer, banned in FORBIDDEN.items():
        for py in Path(layer).rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            for bad in banned:
                assert f"import {bad}" not in text, f"{py} imports {bad}"
