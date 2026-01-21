from pathlib import Path

CORE_FORBIDDEN_SNIPPETS = (
    "open(",
    "pathlib",
    "Path(",
)


def test_core_has_no_filesystem_access() -> None:
    for py in Path("core").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert not any(snippet in text for snippet in CORE_FORBIDDEN_SNIPPETS), f"{py} includes filesystem access"
