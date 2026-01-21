import ast
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml

RULES_PATH = Path("scripts/arch/import_rules.yaml")


class LayerRule(TypedDict, total=False):
    path: str
    forbidden_imports: list[str]
    allow_any: bool


class RulesConfig(TypedDict):
    layers: dict[str, LayerRule]


rules = cast(RulesConfig, yaml.safe_load(RULES_PATH.read_text(encoding="utf-8")))


def detect_layer(path: Path) -> tuple[str | None, LayerRule | None]:
    for layer, rule in rules["layers"].items():
        rule_path = rule.get("path")
        if rule_path and path.as_posix().startswith(rule_path):
            return layer, rule
    return None, None


def check_import(path: Path, module: str | None, rule: LayerRule) -> None:
    if not module:
        return
    for forbidden in rule.get("forbidden_imports", []):
        if module.startswith(forbidden):
            raise SystemExit(f"[ARCH VIOLATION] {path}: illegal import '{module}'")


def main() -> None:
    for file in sys.argv[1:]:
        path = Path(file)
        _layer, rule = detect_layer(path)
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
