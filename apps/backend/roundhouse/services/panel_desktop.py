from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Any, cast
import zipfile

import httpx

from roundhouse.settings import RoundhouseSettings


@dataclass(frozen=True)
class PanelDesktopInstallResult:
    node_id: str
    install_dir: str
    version: str
    asset_name: str


@dataclass(frozen=True)
class PanelDesktopProcessStatus:
    node_id: str
    running: bool
    pid: int | None
    started_at: datetime | None
    executable: str | None
    return_code: int | None


@dataclass
class _DesktopProcess:
    process: subprocess.Popen[str]
    started_at: datetime
    executable: str


class PanelDesktopManager:
    def __init__(self, settings: RoundhouseSettings) -> None:
        self._settings = settings
        self._processes: dict[str, _DesktopProcess] = {}

    def _github_headers(self) -> dict[str, str]:
        token = self._settings.panel_release_token
        if not token:
            return {"Accept": "application/vnd.github+json"}
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
        }

    def _resolve_release_asset_url(self, repo: str, tag: str, asset_name: str) -> str:
        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        with httpx.Client(timeout=20) as client:
            response = client.get(url, headers=self._github_headers())
            response.raise_for_status()
            payload = response.json()
        assets = payload.get("assets", [])
        for asset in assets:
            if asset.get("name") == asset_name:
                return cast(str, asset.get("browser_download_url"))
        raise ValueError("Release asset not found")

    def _download_asset(self, url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=60) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                with dest.open("wb") as handle:
                    for chunk in response.iter_bytes():
                        handle.write(chunk)

    def _extract_zip(self, zip_path: Path, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target_dir)

    def install_from_release(
        self,
        node_id: str,
        repo: str,
        tag: str,
        asset_name: str,
        asset_url: str | None = None,
    ) -> PanelDesktopInstallResult:
        install_root = self._settings.panel_install_dir
        if not install_root:
            raise ValueError("panel_install_dir not configured")
        resolved_url = asset_url or self._resolve_release_asset_url(repo, tag, asset_name)
        install_dir = Path(install_root) / node_id / tag
        archive_path = install_dir / asset_name
        self._download_asset(resolved_url, archive_path)
        if not archive_path.suffix.lower().endswith("zip"):
            raise ValueError("Only .zip assets are supported")
        self._extract_zip(archive_path, install_dir)
        return PanelDesktopInstallResult(
            node_id=node_id,
            install_dir=str(install_dir),
            version=tag,
            asset_name=asset_name,
        )

    def _find_executable(self, install_dir: Path, executable_name: str) -> Path:
        direct = install_dir / executable_name
        if direct.exists():
            return direct
        for path in install_dir.rglob(executable_name):
            if path.is_file():
                return path
        raise FileNotFoundError(f"Executable not found: {executable_name}")

    def start(self, node_id: str, executable_name: str) -> PanelDesktopProcessStatus:
        record = self._processes.get(node_id)
        if record and record.process.poll() is None:
            return self.status(node_id)
        if not executable_name:
            executable_name = self._settings.panel_desktop_executable or "ha_panel_sim"
        install_root = self._settings.panel_install_dir
        if not install_root:
            raise ValueError("panel_install_dir not configured")
        install_dir = Path(install_root) / node_id
        if not install_dir.exists():
            raise FileNotFoundError("Install directory not found")
        latest_dir = max(install_dir.iterdir(), key=lambda p: p.stat().st_mtime)
        executable_path = self._find_executable(latest_dir, executable_name)
        process = subprocess.Popen([str(executable_path)], cwd=latest_dir, text=True)
        entry = _DesktopProcess(
            process=process,
            started_at=datetime.now(),
            executable=str(executable_path),
        )
        self._processes[node_id] = entry
        return self.status(node_id)

    def stop(self, node_id: str) -> PanelDesktopProcessStatus:
        record = self._processes.get(node_id)
        if not record:
            return PanelDesktopProcessStatus(
                node_id=node_id,
                running=False,
                pid=None,
                started_at=None,
                executable=None,
                return_code=None,
            )
        record.process.terminate()
        record.process.wait(timeout=10)
        return self.status(node_id)

    def status(self, node_id: str) -> PanelDesktopProcessStatus:
        record = self._processes.get(node_id)
        if not record:
            return PanelDesktopProcessStatus(
                node_id=node_id,
                running=False,
                pid=None,
                started_at=None,
                executable=None,
                return_code=None,
            )
        return_code = record.process.poll()
        running = return_code is None
        return PanelDesktopProcessStatus(
            node_id=node_id,
            running=running,
            pid=record.process.pid if running else None,
            started_at=record.started_at,
            executable=record.executable,
            return_code=return_code,
        )


_manager: PanelDesktopManager | None = None


def get_panel_desktop_manager(settings: RoundhouseSettings) -> PanelDesktopManager:
    global _manager
    if _manager is None:
        _manager = PanelDesktopManager(settings)
    return _manager
