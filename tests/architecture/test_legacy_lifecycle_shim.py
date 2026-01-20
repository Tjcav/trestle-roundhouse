from __future__ import annotations

import types
from importlib.machinery import SourceFileLoader
from pathlib import Path


def test_no_legacy_lifecycle_implementation() -> None:
    root = Path(__file__).resolve().parents[2]
    legacy_path = root / "trestle-dev-tools_legacy_backend" / "roundhouse" / "panel_lifecycle.py"
    module_name = "legacy_panel_lifecycle_shim"
    loader = SourceFileLoader(module_name, str(legacy_path))
    module = types.ModuleType(module_name)
    loader.exec_module(module)
    assert not hasattr(module, "PanelLifecycleManager")
