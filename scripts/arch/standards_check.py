import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN_PATH = ROOT / ".trestle" / "standards.version"
SNAPSHOT_PATH = ROOT / ".trestle" / "standards.snapshot.json"


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if not PIN_PATH.exists():
        raise SystemExit("Missing .trestle/standards.version")

    version = PIN_PATH.read_text(encoding="utf-8").strip()
    if not version or not version.startswith("v"):
        raise SystemExit("standards.version must be a non-empty vX.Y.Z tag")

    if not SNAPSHOT_PATH.exists():
        raise SystemExit("Missing .trestle/standards.snapshot.json")

    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    files = snapshot.get("files", {})
    if not files:
        raise SystemExit("Snapshot has no files")

    errors: list[str] = []
    for rel_path, expected in files.items():
        path = ROOT / rel_path
        if not path.exists():
            errors.append(f"Missing file: {rel_path}")
            continue
        actual = _sha256(path)
        if actual != expected:
            errors.append(f"Drift detected: {rel_path}")

    if errors:
        message = "\n".join(errors)
        raise SystemExit(f"Standards drift detected for {version}:\n{message}")


if __name__ == "__main__":
    main()
