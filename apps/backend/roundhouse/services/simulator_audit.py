from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

AUDIT_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "simulator-selection-log.jsonl"


def log_selection(artifact_name: str, user: str = "system") -> None:
    entry = {
        "artifact_name": artifact_name,
        "user": user,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_audit_log() -> List[Dict[str, Any]]:
    if not AUDIT_LOG_PATH.exists():
        return []
    with AUDIT_LOG_PATH.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
