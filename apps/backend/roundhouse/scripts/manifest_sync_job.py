#!/usr/bin/env python3
"""
Background job to periodically sync the build-artifact-manifest.json from GitHub Releases.
Can be run as a cron job or service.
"""

import time
from typing import NoReturn

from roundhouse.services.manifest_sync import fetch_manifest_from_github, get_manifest_sync_config

SYNC_INTERVAL_SECONDS = 3600  # 1 hour


def main() -> NoReturn:
    while True:
        repo, release_tag, asset_name, token = get_manifest_sync_config()
        if repo:
            ok = fetch_manifest_from_github(repo, release_tag, asset_name, token)
            if ok:
                print(f"[manifest-sync] Refreshed manifest from {repo} ({release_tag})")
            else:
                print(f"[manifest-sync] Failed to refresh manifest from {repo} ({release_tag})")
        else:
            print("[manifest-sync] No repo configured; skipping.")
        time.sleep(SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
