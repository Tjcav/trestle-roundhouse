import ast
import sys
from pathlib import Path

FORBIDDEN_REFERENCES = (
    "trestle-dev-tools_legacy_backend",
    "trestle-roundhouse-frontend_legacy",
)

CORE_FORBIDDEN_SNIPPETS = (
    "open(",
    "pathlib",
    "Path(",
)

ALLOWED_PATH_PREFIXES = (
    "trestle-dev-tools_legacy_backend/",
    "trestle-roundhouse-frontend_legacy/",
)


def _is_legacy_path(path: Path) -> bool:
    return path.as_posix().startswith(ALLOWED_PATH_PREFIXES)


def _contains_forbidden_reference(text: str) -> bool:
    return any(ref in text for ref in FORBIDDEN_REFERENCES)


def main() -> None:
    for file in sys.argv[1:]:
        path = Path(file)
        if path.as_posix() in {
            "scripts/arch/path_check.py",
            "tests/architecture/test_legacy_lifecycle_shim.py",
        }:
            continue
        if _is_legacy_path(path):
            continue
        if path.suffix != ".py":
            continue
        text = path.read_text(encoding="utf-8")
        if _contains_forbidden_reference(text):
            raise SystemExit(f"[ARCH VIOLATION] {path}: legacy reference is forbidden")
        if path.as_posix().startswith("core/"):
            if any(snippet in text for snippet in CORE_FORBIDDEN_SNIPPETS):
                raise SystemExit(f"[ARCH VIOLATION] {path}: core must not access filesystem")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if _contains_forbidden_reference(module):
                    raise SystemExit(f"[ARCH VIOLATION] {path}: illegal legacy import '{module}'")
            elif isinstance(node, ast.Import):
                for name in node.names:
                    if _contains_forbidden_reference(name.name):
                        raise SystemExit(f"[ARCH VIOLATION] {path}: illegal legacy import '{name.name}'")


if __name__ == "__main__":
    main()
