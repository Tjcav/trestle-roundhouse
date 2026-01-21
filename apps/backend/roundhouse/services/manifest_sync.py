from __future__ import annotations

import os
from pathlib import Path

import requests

from apps.backend.roundhouse.settings import RoundhouseSettings
from roundhouse.settings import load_settings

MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "build-artifact-manifest.json"


def fetch_manifest_from_github(repo: str, release_tag: str, asset_name: str, token: str | None = None) -> bool:
    """
    Download the manifest asset from a GitHub release and save to MANIFEST_PATH.
    Returns True if successful, False otherwise.
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/tags/{release_tag}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    resp = requests.get(api_url, headers=headers)
    if resp.status_code != 200:
        return False
    release = resp.json()
    asset = next((a for a in release.get("assets", []) if a["name"] == asset_name), None)
    if not asset:
        return False
    download_url = asset["browser_download_url"]
    asset_resp = requests.get(download_url, headers=headers, stream=True)
    if asset_resp.status_code != 200:
        return False
    with MANIFEST_PATH.open("wb") as f:
        for chunk in asset_resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return True


def get_manifest_sync_config() -> tuple[str | None, str, str, str | None]:
    settings: RoundhouseSettings = load_settings()
    repo = os.getenv("ROUNDHOUSE_PANEL_REPO")
    release_tag = os.getenv("ROUNDHOUSE_PANEL_RELEASE_TAG", "latest")
    asset_name = os.getenv("ROUNDHOUSE_PANEL_MANIFEST_NAME", "build-artifact-manifest.json")
    token = settings.panel_release_token
    return repo, release_tag, asset_name, token
