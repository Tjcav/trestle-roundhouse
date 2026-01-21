from __future__ import annotations

from typing import Any, Optional

# Example: these would be provided by the environment or config
CURRENT_HW_REV = "A"
CURRENT_PROTOCOL_VERSION = "1.0"


def check_compatibility(
    artifact: dict[str, Any], hw_rev: str = CURRENT_HW_REV, protocol_version: str = CURRENT_PROTOCOL_VERSION
) -> tuple[bool, Optional[str]]:
    """
    Returns (is_compatible, reason_if_not)
    """
    compat = artifact.get("compatibility", {})
    # HW revision check
    hw_ok = True
    if "hw_rev" in compat:
        allowed = compat["hw_rev"]
        if isinstance(allowed, list):
            hw_ok = hw_rev in allowed
        else:
            hw_ok = hw_rev == allowed
        if not hw_ok:
            return False, f"Incompatible hardware revision: requires {allowed}, have {hw_rev}"
    # Protocol version check
    proto_ok = True
    if "protocol_version" in compat:
        allowed = compat["protocol_version"]
        if isinstance(allowed, list):
            proto_ok = protocol_version in allowed
        else:
            proto_ok = protocol_version == allowed
        if not proto_ok:
            return False, f"Incompatible protocol version: requires {allowed}, have {protocol_version}"
    return True, None
