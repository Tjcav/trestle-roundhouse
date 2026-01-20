import ast
import sys
from pathlib import Path

import yaml

RULES_PATH = Path("scripts/arch/import_rules.yaml")


rules = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))


def detect_layer(path: Path) -> tuple[str | None, dict | None]:
    for layer, rule in rules["layers"].items():
        if path.as_posix().startswith(rule["path"]):
            return layer, rule
    return None, None


def check_import(path: Path, module: str | None, rule: dict) -> None:
    if not module:
        return
    for forbidden in rule.get("forbidden_imports", []):
        if module.startswith(forbidden):
            raise SystemExit(f"[ARCH VIOLATION] {path}: illegal import '{module}'")


def main() -> None:
    for file in sys.argv[1:]:
        path = Path(file)
        layer, rule = detect_layer(path)
        if not rule or rule.get("allow_any"):
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    check_import(path, n.name, rule)
            elif isinstance(node, ast.ImportFrom):
                check_import(path, node.module, rule)


if __name__ == "__main__":
    main()
