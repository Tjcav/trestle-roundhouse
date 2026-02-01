from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, cast

import requests
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from apps.backend.roundhouse.settings import RoundhouseSettings
from roundhouse.settings import load_settings

MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "build-artifact-manifests.json"
_manifest_cache: list["BuildManifest"] | None = None
_manifest_mtime: float | None = None


class ManifestError(RuntimeError):
    def __init__(self, message: str, code: str = "manifest_error", status_code: int = 500) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _raise_for_repo_response(resp: requests.Response) -> None:
    if resp.status_code == 401:
        raise ManifestError(
            "GitHub authentication failed for repository",
            code="REPO_AUTH_FAILED",
            status_code=401,
        )
    if resp.status_code == 403:
        raise ManifestError(
            "GitHub token does not have access to this repository",
            code="REPO_FORBIDDEN",
            status_code=403,
        )
    if resp.status_code == 404:
        raise ManifestError(
            "Repository or release not found",
            code="REPO_NOT_FOUND",
            status_code=404,
        )
    if resp.status_code >= 400:
        raise ManifestError(
            "Repository URL is invalid or unreachable",
            code="REPO_INVALID_URL",
            status_code=400,
        )


def _release_api_url(repo: str, release_tag: str) -> str:
    if release_tag == "latest":
        return f"https://api.github.com/repos/{repo}/releases/latest"
    return f"https://api.github.com/repos/{repo}/releases/tags/{release_tag}"


class ManifestArtifactFile(BaseModel):
    filename: str
    sha256: str | None = None
    entrypoint: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, value: Any) -> Dict[str, Any] | Any:
        if isinstance(value, str):
            return {"filename": value}
        if isinstance(value, dict) and "filename" not in value and "name" in value:
            source = cast(Dict[str, Any], value)
            normalized: Dict[str, Any] = {"filename": source.get("name")}
            for key, item in source.items():
                if key == "name":
                    continue
                normalized[key] = item
            return normalized
        if isinstance(value, dict):
            return cast(Dict[str, Any], value)
        return value


class BuildManifest(BaseModel):
    artifact: str
    platform: str
    version: str
    release_tag: str
    artifacts: List[ManifestArtifactFile]

    @field_validator("artifacts", mode="before")
    @classmethod
    def _normalize_artifacts(cls, value: Any) -> list[ManifestArtifactFile] | Any:
        if isinstance(value, list):
            return cast(list[Dict[str, Any] | str], value)
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        return value


def fetch_manifest_from_github(repo: str, release_tag: str, asset_name: str, token: str | None = None) -> bool:
    """
    Download the manifest asset from a GitHub release and save to MANIFEST_PATH.
    Returns True if successful, False otherwise.
    """
    api_url = _release_api_url(repo, release_tag)
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        resp = requests.get(api_url, headers=headers, timeout=20)
    except requests.RequestException as exc:
        raise ManifestError(
            "Repository URL is invalid or unreachable",
            code="REPO_INVALID_URL",
            status_code=400,
        ) from exc
    _raise_for_repo_response(resp)
    release = resp.json()
    assets = [a for a in release.get("assets", []) if a.get("name", "").endswith(asset_name)]
    if not assets:
        raise ManifestError(
            "No canonical manifest found in release assets",
            code="MANIFEST_NOT_FOUND",
            status_code=404,
        )
    manifests: list[dict[str, Any]] = []
    for asset in assets:
        download_url = asset.get("url") or asset.get("browser_download_url")
        download_headers = headers.copy()
        if asset.get("url"):
            download_headers["Accept"] = "application/octet-stream"
        try:
            asset_resp = requests.get(download_url, headers=download_headers, timeout=20)
        except requests.RequestException as exc:
            raise ManifestError(
                "Failed to download manifest asset",
                code="MANIFEST_NOT_FOUND",
                status_code=404,
            ) from exc
        if asset_resp.status_code == 404:
            raise ManifestError(
                "No canonical manifest found in release assets",
                code="MANIFEST_NOT_FOUND",
                status_code=404,
            )
        if asset_resp.status_code >= 400:
            raise ManifestError(
                "Failed to download manifest asset",
                code="MANIFEST_NOT_FOUND",
                status_code=404,
            )
        try:
            manifests.append(asset_resp.json())
        except json.JSONDecodeError as exc:
            raise ManifestError(
                "Simulator manifest is malformed",
                code="MANIFEST_INVALID_JSON",
                status_code=422,
            ) from exc
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifests, f)
    return True


def load_manifest_from_disk() -> List[Dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        raise ManifestError("Simulator manifest not found", code="MANIFEST_NOT_FOUND", status_code=404)
    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise ManifestError(
            "Simulator manifest is malformed",
            code="MANIFEST_INVALID_JSON",
            status_code=422,
        ) from exc


def _validate_manifests(manifests: List[Dict[str, Any]]) -> list[BuildManifest]:
    parsed: list[BuildManifest] = []
    try:
        for manifest in manifests:
            parsed.append(BuildManifest.model_validate(manifest))
    except ValidationError as exc:
        raise ManifestError(
            "Simulator manifest failed schema validation",
            code="MANIFEST_SCHEMA_INVALID",
            status_code=422,
        ) from exc
    return parsed


def get_manifest(repo: str | None, release_tag: str, asset_name: str, token: str | None) -> list[BuildManifest]:
    global _manifest_cache, _manifest_mtime
    if not repo:
        raise ManifestError("Simulator manifest source not configured", code="manifest_unconfigured")
    if MANIFEST_PATH.exists():
        mtime = MANIFEST_PATH.stat().st_mtime
        if _manifest_cache is not None and _manifest_mtime == mtime:
            return _manifest_cache
        manifests = _validate_manifests(load_manifest_from_disk())
        _manifest_cache = manifests
        _manifest_mtime = mtime
        return manifests
    fetch_manifest_from_github(repo, release_tag, asset_name, token)
    manifests = _validate_manifests(load_manifest_from_disk())
    _manifest_cache = manifests
    _manifest_mtime = MANIFEST_PATH.stat().st_mtime
    return manifests


def get_manifest_sync_config() -> tuple[str | None, str, str, str | None]:
    settings: RoundhouseSettings = load_settings()
    repo = os.getenv("ROUNDHOUSE_PANEL_REPO")
    release_tag = os.getenv("ROUNDHOUSE_PANEL_RELEASE_TAG", "latest")
    asset_name = os.getenv("ROUNDHOUSE_PANEL_MANIFEST_NAME", "build-artifact-manifest.json")
    token = settings.panel_release_token
    return repo, release_tag, asset_name, token
