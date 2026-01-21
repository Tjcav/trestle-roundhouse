from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

SELECTION_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "simulator-selection.json"


def get_selected_version() -> Optional[str]:
    if not SELECTION_PATH.exists():
        return None
    with SELECTION_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("artifact_name")


def set_selected_version(artifact_name: str) -> None:
    with SELECTION_PATH.open("w", encoding="utf-8") as f:
        json.dump({"artifact_name": artifact_name}, f)
