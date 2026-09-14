import os
import re
import json
import urllib.request
import urllib.error
import tempfile
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from .config import APP_VERSION, GITHUB_RELEASES_API

def parse_version_tuple(version_str: str) -> tuple[int, ...]:
    """
    Parses semantic version strings like 'v3.9.5', '3.9.5', 'v3.10.1-beta'
    into an integer tuple for reliable comparison: (3, 9, 5).
    """
    if not version_str:
        return (0, 0, 0)
    clean = version_str.strip().lstrip("vV")
    m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", clean)
    if m:
        parts = [int(p) if p is not None else 0 for p in m.groups()]
        return tuple(parts)
    return (0, 0, 0)

def check_for_updates_sync(timeout: float = 6.0) -> dict:
    """
    Queries GitHub Releases API synchronously.
    Returns a dictionary containing update details and availability.
    """
    current_ver = APP_VERSION
    current_tuple = parse_version_tuple(current_ver)

    req = urllib.request.Request(
        GITHUB_RELEASES_API,
        headers={
            "User-Agent": f"RawView-App/{current_ver}",
            "Accept": "application/vnd.github.v3+json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return {
                    "has_update": False,
                    "error": f"HTTP {resp.status}",
                    "current_version": current_ver
                }
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {
            "has_update": False,
            "error": str(e),
            "current_version": current_ver
        }

    tag_name = payload.get("tag_name", "").strip()
    remote_tuple = parse_version_tuple(tag_name)
    has_update = remote_tuple > current_tuple

    # Locate the setup executable asset
    download_url = ""
    asset_name = ""
    asset_size = 0
    assets = payload.get("assets", [])
    
    # Priority 1: Exact installer name matching *Setup.exe
    for a in assets:
        name = a.get("name", "")
        if name.lower().endswith("setup.exe") or (name.lower().endswith(".exe") and "rawview" in name.lower()):
            download_url = a.get("browser_download_url", "")
            asset_name = name
            asset_size = a.get("size", 0)
            break

    # Priority 2: Any .exe asset
    if not download_url:
        for a in assets:
            name = a.get("name", "")
            if name.lower().endswith(".exe"):
                download_url = a.get("browser_download_url", "")
                asset_name = name
                asset_size = a.get("size", 0)
                break

    return {
        "has_update": has_update,
        "latest_version": tag_name if tag_name else current_ver,
        "current_version": current_ver,
        "release_name": payload.get("name", tag_name),
        "release_notes": payload.get("body", ""),
        "published_at": payload.get("published_at", ""),
        "html_url": payload.get("html_url", ""),
        "download_url": download_url,
        "asset_name": asset_name,
        "asset_size": asset_size,
        "error": None
    }

class UpdateCheckWorker(QThread):
    """Background worker thread for querying GitHub Releases API."""
    update_checked = pyqtSignal(dict)
    check_failed = pyqtSignal(str)

    def __init__(self, timeout: float = 6.0, parent=None):
        super().__init__(parent)
        self.timeout = timeout

    def run(self):
        try:
            info = check_for_updates_sync(self.timeout)
            if info.get("error"):
                self.check_failed.emit(info["error"])
            else:
                self.update_checked.emit(info)
        except Exception as e:
            self.check_failed.emit(str(e))

class UpdateDownloadWorker(QThread):
    """Background worker thread for downloading the setup installer with live progress."""
    progress = pyqtSignal(int, int, float) # (downloaded_bytes, total_bytes, percent)
    finished = pyqtSignal(str)           # (saved_file_path)
    error = pyqtSignal(str)              # (error_message)

    def __init__(self, download_url: str, asset_name: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.asset_name = asset_name or "RawView_Setup.exe"
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if not self.download_url:
            self.error.emit("No valid download URL provided for installer.")
            return

        temp_dir = Path(tempfile.gettempdir()) / "RawView_Update"
        temp_dir.mkdir(parents=True, exist_ok=True)
        dest_path = temp_dir / self.asset_name

        req = urllib.request.Request(
            self.download_url,
            headers={"User-Agent": f"RawView-Downloader/{APP_VERSION}"}
        )

        try:
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                total_bytes = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024 # 64 KB

                with open(dest_path, "wb") as f_out:
                    while True:
                        if self._is_cancelled:
                            dest_path.unlink(missing_ok=True)
                            self.error.emit("Download cancelled by user.")
                            return
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        downloaded += len(chunk)
                        pct = (downloaded / total_bytes * 100.0) if total_bytes > 0 else 0.0
                        self.progress.emit(downloaded, total_bytes, pct)

            self.finished.emit(str(dest_path))
        except Exception as e:
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except Exception:
                    pass
            self.error.emit(str(e))
