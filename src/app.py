import os
import sys
import argparse
import ctypes
from ctypes import wintypes
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import (
    QObject, pyqtSignal, QRunnable, QThreadPool, Qt, QAbstractNativeEventFilter
)
from PyQt6.QtGui import QFont, QColor, QPalette

from src.core.config import (
    load_config, save_config, APP_NAME, APP_VERSION, APP_MUTEX_NAME
)
from src.core.cache import MemoryCache, DiskCache
from src.core.decoders import DecoderManager, PreviewResult
from src.core.explorer_hook import ExplorerHoverMonitor
from src.core.icons import create_app_icon
from src.ui.preview_window import FloatingPreviewHUD
from src.ui.tray_icon import TrayManager
from src.ui.status_hud import StatusToastHUD

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

class GlobalHotkeyFilter(QAbstractNativeEventFilter, QObject):
    hotkey_triggered = pyqtSignal()

    def __init__(self, hotkey_id=9876, parent=None):
        QObject.__init__(self, parent)
        self.hotkey_id = hotkey_id

    def nativeEventFilter(self, eventType, message):
        if eventType in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            try:
                msg = wintypes.MSG.from_address(int(message))
                # WM_HOTKEY = 0x0312
                if msg.message == 0x0312 and msg.wParam == self.hotkey_id:
                    self.hotkey_triggered.emit()
                    return True, 0
            except Exception:
                pass
        return False, 0

class ConfigSaveRunnable(QRunnable):
    def __init__(self, config: dict):
        super().__init__()
        self.config = dict(config)

    def run(self):
        try:
            save_config(self.config)
        except Exception:
            pass

class DecodeWorkerSignals(QObject):
    finished = pyqtSignal(str, object, int, int) # (file_path, PreviewResult, cursor_x, cursor_y)
    error = pyqtSignal(str, str) # (file_path, error_msg)

class DecodeRunnable(QRunnable):
    """Background decoding task for cache-missed local & FTP files to prevent any UI stutter."""
    def __init__(self, file_path: str, cursor_x: int, cursor_y: int, max_size: int, memory_cache: MemoryCache, disk_cache: DiskCache):
        super().__init__()
        self.file_path = file_path
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        self.max_size = max_size
        self.memory_cache = memory_cache
        self.disk_cache = disk_cache
        self.signals = DecodeWorkerSignals()

    def run(self):
        try:
            is_ftp = self.file_path.startswith("ftp://") or self.file_path.startswith("ftps://")
            
            if is_ftp:
                import urllib.request
                import urllib.parse
                import hashlib

                url_hash = hashlib.md5(self.file_path.encode('utf-8')).hexdigest()
                temp_ftp_dir = os.path.join(self.disk_cache.cache_dir, "ftp_temp")
                os.makedirs(temp_ftp_dir, exist_ok=True)
                ext = Path(urllib.parse.urlparse(self.file_path).path).suffix.lower()
                temp_file = os.path.join(temp_ftp_dir, f"{url_hash}{ext}")

                if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                    req = urllib.request.Request(self.file_path)
                    with urllib.request.urlopen(req, timeout=4.0) as resp:
                        with open(temp_file, "wb") as f_out:
                            # Stream first 25MB for preview
                            chunk = resp.read(25 * 1024 * 1024)
                            f_out.write(chunk)

                actual_size = os.path.getsize(temp_file)
                res = DecoderManager.decode(temp_file, max_size=self.max_size)
                res.file_size = actual_size
                self.memory_cache.put(self.file_path, 0, 0, res)
                self.signals.finished.emit(self.file_path, res, self.cursor_x, self.cursor_y)
                return

            mtime = os.path.getmtime(self.file_path)
            size = os.path.getsize(self.file_path)

            # Check L2 Disk Cache
            cached_disk = self.disk_cache.get(self.file_path, mtime, size)
            if cached_disk:
                pil_img, meta = cached_disk
                from src.core.decoders import pil_to_qimage
                qim = pil_to_qimage(pil_img)
                is_vid = meta.get("is_video", False)
                res = PreviewResult(
                    qimage=qim,
                    width=meta.get("width", 0),
                    height=meta.get("height", 0),
                    mode=meta.get("mode", ""),
                    format_name=meta.get("format", ""),
                    file_size=size,
                    extra_info=meta.get("extra", ""),
                    is_video=is_vid,
                    video_path=self.file_path if is_vid else ""
                )
                self.memory_cache.put(self.file_path, mtime, size, res)
                self.signals.finished.emit(self.file_path, res, self.cursor_x, self.cursor_y)
                return

            # Zero-Lag Decoding
            res = DecoderManager.decode(self.file_path, max_size=self.max_size)

            # Populate L1 RAM cache
            self.memory_cache.put(self.file_path, mtime, size, res)

            # Emit preview immediately to UI (Zero-Lag!)
            self.signals.finished.emit(self.file_path, res, self.cursor_x, self.cursor_y)

            # Save to L2 Disk asynchronously
            try:
                from PIL import Image
                from PyQt6.QtCore import QBuffer, QIODevice
                buf = QBuffer()
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                res.qimage.save(buf, "PNG")
                png_bytes = buf.data().data()
                buf.close()
                if png_bytes:
                    import io
                    pil_img = Image.open(io.BytesIO(png_bytes))
                    meta = {
                        "width": res.width,
                        "height": res.height,
                        "mode": res.mode,
                        "format": res.format_name,
                        "extra": res.extra_info,
                        "is_video": res.is_video
                    }
                    self.disk_cache.put(self.file_path, mtime, size, pil_img, meta)
            except Exception:
                pass

        except Exception as e:
            self.signals.error.emit(self.file_path, str(e))

class RawViewApp(QObject):
    """Main application controller managing lifecycle and signal connections."""
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.memory_cache = MemoryCache(max_items=128)
        self.disk_cache = DiskCache(max_size_mb=config.get("cache_max_mb", 500))
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)

        # 1. Floating Preview HUD
        self.preview_hud = FloatingPreviewHUD(self.config)

        # 2. Explorer Hover Monitor
        self.hover_monitor = ExplorerHoverMonitor(self.config)
        self.hover_monitor.file_hovered.connect(self._on_file_hovered)
        self.hover_monitor.hover_cleared.connect(self._on_hover_cleared)
        self.hover_monitor.space_pin_requested.connect(self.preview_hud.toggle_pin)
        self.hover_monitor.escape_requested.connect(self.preview_hud.dismiss)
        self.hover_monitor.toggle_enabled_requested.connect(self._on_toggle_enabled)

        # Connect bidirectional preview state for global key interception
        self.preview_hud.visibility_changed.connect(self.hover_monitor.set_preview_visible)
        self.preview_hud.pin_state_changed.connect(self.hover_monitor.set_preview_pinned)

        # 3. System Tray Manager
        self.tray_manager = TrayManager(self.config)
        self.tray_manager.config_updated.connect(self._on_config_updated)
        self.tray_manager.quit_requested.connect(self.shutdown)
        self.preview_hud.open_settings_requested.connect(self.tray_manager.show_settings)
        self.tray_manager.show()

        # 4. Native OS Global Hotkey (Ctrl + `) with Windows Kernel Filter for 0ms response
        self.hotkey_id = 9876
        self.hotkey_filter = GlobalHotkeyFilter(hotkey_id=self.hotkey_id)
        self.hotkey_filter.hotkey_triggered.connect(self._on_toggle_enabled)
        QApplication.instance().installNativeEventFilter(self.hotkey_filter)

        # VK_OEM_3 = 0xC0 (` / ~ key), MOD_CONTROL = 0x0002, MOD_NOREPEAT = 0x4000
        self.hotkey_registered = bool(
            user32.RegisterHotKey(None, self.hotkey_id, 0x0002 | 0x4000, 0xC0)
        )

        # Start Hover Monitoring
        self.hover_monitor.start()

    def _on_file_hovered(self, file_path: str, screen_x: int, screen_y: int):
        is_ftp = file_path.startswith("ftp://") or file_path.startswith("ftps://")
        if not is_ftp and not os.path.exists(file_path):
            return

        try:
            mtime = 0 if is_ftp else os.path.getmtime(file_path)
            size = 0 if is_ftp else os.path.getsize(file_path)

            # Check L1 Memory Cache (Instant sub-millisecond response)
            cached_res = self.memory_cache.get(file_path, mtime, size)
            if cached_res:
                self.preview_hud.display_preview(file_path, cached_res, screen_x, screen_y)
                return

            # Dispatch background worker
            worker = DecodeRunnable(
                file_path=file_path,
                cursor_x=screen_x,
                cursor_y=screen_y,
                max_size=self.config.get("preview_max_size", 640),
                memory_cache=self.memory_cache,
                disk_cache=self.disk_cache
            )
            worker.signals.finished.connect(self._on_decode_finished)
            worker.signals.error.connect(self._on_decode_error)
            self.thread_pool.start(worker)

        except Exception as e:
            print(f"Error handling hover for {file_path}: {e}")

    def _on_decode_finished(self, file_path: str, result: PreviewResult, cursor_x: int, cursor_y: int):
        # Only show if still hovering over the same file or pinned
        if self.hover_monitor.active_file_path == file_path or self.preview_hud.is_pinned:
            self.preview_hud.display_preview(file_path, result, cursor_x, cursor_y)

    def _on_decode_error(self, file_path: str, error_msg: str):
        print(f"[RawView] Decode error for {file_path}: {error_msg}")

    def _on_hover_cleared(self):
        if not self.preview_hud.is_pinned:
            self.preview_hud.dismiss()

    def _on_config_updated(self, new_config: dict):
        prev_enabled = self.config.get("enabled", True)
        self.config = new_config
        self.hover_monitor.update_config(new_config)
        self.preview_hud.config = new_config
        new_enabled = new_config.get("enabled", True)
        if new_enabled != prev_enabled:
            StatusToastHUD.show_status(new_enabled)

    def _on_toggle_enabled(self):
        """Handles Ctrl+` global hotkey: toggles hover preview enabled state system-wide with instant HUD."""
        import time
        now = time.time()
        if now - getattr(self, "_last_toggle_time", 0.0) < 0.3:
            return
        self._last_toggle_time = now

        new_state = not self.config.get("enabled", True)
        self.config["enabled"] = new_state
        self.hover_monitor.update_config(self.config)
        self.preview_hud.config = self.config
        
        # Sync tray menu checkbox
        self.tray_manager.toggle_action.setChecked(new_state)
        
        # Dismiss any active preview when disabling
        if not new_state:
            self.preview_hud.dismiss()

        # Instant On-Screen Glassmorphic HUD Badge (<5ms response, zero lag)
        StatusToastHUD.show_status(new_state)

        # Async background config save so disk I/O does not delay responsiveness
        self.thread_pool.start(ConfigSaveRunnable(self.config))

    def shutdown(self):
        if getattr(self, "hotkey_registered", False):
            try:
                user32.UnregisterHotKey(None, self.hotkey_id)
            except Exception:
                pass
        if getattr(self, "hotkey_filter", None):
            try:
                QApplication.instance().removeNativeEventFilter(self.hotkey_filter)
            except Exception:
                pass
        self.hover_monitor.stop()
        self.preview_hud.close()
        QApplication.quit()

def check_single_instance() -> bool:
    """Uses a named Win32 mutex to enforce a single running instance."""
    mutex = kernel32.CreateMutexW(None, True, APP_MUTEX_NAME)
    last_error = kernel32.GetLastError()
    # ERROR_ALREADY_EXISTS = 183
    if last_error == 183:
        if mutex:
            kernel32.CloseHandle(mutex)
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument("--minimized", action="store_true", help="Start minimized to System Tray")
    parser.add_argument("--settings", action="store_true", help="Open settings dialog immediately")
    args = parser.parse_args()

    # Enforce Single Instance
    if not check_single_instance():
        print(f"{APP_NAME} is already running in background.")
        sys.exit(0)

    # Initialize Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(create_app_icon(128))

    # Set default modern font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Load configuration
    config = load_config()

    # Start RawView Engine
    rawview = RawViewApp(config)

    if args.settings:
        rawview.tray_manager.show_settings()

    print(f"{APP_NAME} {APP_VERSION} initialized successfully. Monitoring file hover in background.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
