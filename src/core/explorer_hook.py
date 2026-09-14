import os
import sys
import re
import urllib.parse
from pathlib import Path
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32api
import pythoncom
import win32com.client
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QCursor
import uiautomation as auto
from .config import SUPPORTED_EXTENSIONS

def normalize_str(s: str) -> str:
    """Strips whitespace, underscores, hyphens, and dots for fuzzy matching across line-wrapped labels."""
    return re.sub(r'[\s_\-\.]+', '', s.lower())

def parse_shell_url(url: str) -> str:
    """Parses Explorer LocationURL into a clean local path, UNC network path, or FTP URL."""
    if not url:
        return ""
    if url.startswith("ftp://") or url.startswith("ftps://"):
        return url
    if url.startswith("file://"):
        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path)
        if parsed.netloc:
            # UNC path: file://server/share
            return f"\\\\{parsed.netloc}{path}".replace("/", "\\")
        else:
            # Local path: file:///C:/path
            if path.startswith("/") and len(path) > 2 and path[2] == ":":
                path = path[1:]
            return path.replace("/", "\\")
    return url

def detect_extensions_from_type_text(type_text: str) -> list[str]:
    """Infers potential file extensions from Windows Explorer Type column or tooltip text."""
    if not type_text:
        return []
    t = type_text.lower()
    
    # Extract after 'type:' or 'item type:' if present in tooltip
    m = re.search(r"(?:item type|type)\s*:\s*([^\r\n]+)", t)
    target_str = m.group(1).lower().strip() if m else t

    # Photoshop
    if "photoshop" in target_str or "psd" in target_str or "psb" in target_str:
        return [".psd", ".psb"]
    # Illustrator
    if "illustrator" in target_str or "ai artwork" in target_str or "ai file" in target_str:
        return [".ai", ".eps"]
    # InDesign
    if "indesign" in target_str or "indd" in target_str or "indt" in target_str:
        return [".indd", ".indt"]
    # CorelDRAW
    if "coreldraw" in target_str or "cdr" in target_str:
        return [".cdr"]
    # Standard Image Formats (JPG/JPEG, PNG, WebP, GIF, BMP, ICO, TIFF)
    if "jpeg" in target_str or "jpg" in target_str or "jpe" in target_str:
        return [".jpg", ".jpeg", ".jpe"]
    if "png" in target_str or "portable network" in target_str:
        return [".png"]
    if "webp" in target_str:
        return [".webp"]
    if "gif" in target_str:
        return [".gif"]
    if "bmp" in target_str or "bitmap" in target_str or "dib" in target_str:
        return [".bmp", ".dib"]
    if "ico" in target_str or "icon" in target_str:
        return [".ico"]
    if "tiff" in target_str or "tif" in target_str:
        return [".tif", ".tiff"]
    # PDF
    if "pdf" in target_str or "portable document" in target_str or "acrobat" in target_str:
        return [".pdf"]
    # PostScript / EPS
    if "postscript" in target_str or "encapsulated" in target_str or "eps" in target_str:
        return [".eps"]
    # SVG
    if "scalable vector" in target_str or "svg" in target_str:
        return [".svg", ".svgz"]
    # Camera RAW Formats
    if "digital negative" in target_str or "dng" in target_str:
        return [".dng"]
    if "canon" in target_str or "cr2" in target_str or "cr3" in target_str or "crw" in target_str:
        return [".cr2", ".cr3", ".crw"]
    if "nikon" in target_str or "nef" in target_str or "nrw" in target_str:
        return [".nef", ".nrw"]
    if "sony" in target_str or "arw" in target_str or "srf" in target_str or "sr2" in target_str:
        return [".arw", ".srf", ".sr2"]
    if "fujifilm" in target_str or "raf" in target_str:
        return [".raf"]
    if "olympus" in target_str or "orf" in target_str:
        return [".orf", ".ori"]
    if "lumix" in target_str or "panasonic" in target_str or "rw2" in target_str:
        return [".rw2"]
    if "camera raw" in target_str or "raw image" in target_str:
        return [".dng", ".raw", ".cr2", ".cr3", ".nef", ".arw", ".raf", ".orf", ".rw2"]

    # Microsoft Word & RTF
    if "word" in target_str or "docx" in target_str or "docm" in target_str or "dotx" in target_str or "doc " in target_str:
        return [".docx", ".doc", ".docm", ".dotx", ".dot"]
    if "rich text" in target_str or "rtf" in target_str:
        return [".rtf"]

    # Microsoft Excel & CSV
    if "excel" in target_str or "spreadsheet" in target_str or "worksheet" in target_str or "xlsx" in target_str or "xlsm" in target_str or "xlsb" in target_str:
        return [".xlsx", ".xls", ".xlsm", ".xlsb", ".xltx"]
    if "comma separated" in target_str or "csv" in target_str:
        return [".csv"]

    # Microsoft PowerPoint
    if "powerpoint" in target_str or "presentation" in target_str or "slide" in target_str or "pptx" in target_str or "pptm" in target_str or "ppsx" in target_str:
        return [".pptx", ".ppt", ".pptm", ".ppsx", ".potx"]

    # Adobe After Effects & Premiere Pro
    if "after effects" in target_str or "aep" in target_str or "aet" in target_str:
        return [".aep", ".aet", ".aepx"]
    if "premiere" in target_str or "prproj" in target_str or "prset" in target_str:
        return [".prproj", ".prset"]

    # Video Formats
    if "mp4" in target_str or "mpeg-4" in target_str:
        return [".mp4", ".m4v"]
    if "mkv" in target_str or "matroska" in target_str:
        return [".mkv"]
    if "quicktime" in target_str or "mov" in target_str:
        return [".mov"]
    if "avi" in target_str or "audio video interleave" in target_str:
        return [".avi"]
    if "windows media" in target_str or "wmv" in target_str:
        return [".wmv"]
    if "webm" in target_str:
        return [".webm"]
    if "flash video" in target_str or "flv" in target_str:
        return [".flv"]
    if "transport stream" in target_str or "ts video" in target_str:
        return [".ts"]
    if "3gp" in target_str or "3gpp" in target_str:
        return [".3gp"]
    if "video" in target_str or "movie" in target_str or "media file" in target_str or "clip" in target_str:
        return [".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv", ".ts", ".m4v", ".3gp"]
        
    return []

def parse_size_in_kb(size_text: str) -> float | None:
    """Parses size strings like '856 KB', '2,915 KB', '1.69 MB' into numeric KB."""
    if not size_text:
        return None
    clean = size_text.replace(",", "").strip()
    m = re.search(r"([\d\.]+)\s*(kb|mb|gb|bytes|b)?", clean, re.IGNORECASE)
    if not m:
        return None
    try:
        val = float(m.group(1))
        unit = (m.group(2) or "kb").lower()
        if unit == "kb":
            return val
        elif unit == "mb":
            return val * 1024.0
        elif unit == "gb":
            return val * 1024.0 * 1024.0
        elif unit in ("bytes", "b"):
            return val / 1024.0
        return val
    except Exception:
        return None

class ExplorerHoverMonitor(QObject):
    """
    Zero-lag, highly resilient file hover detector.
    Works seamlessly across Windows 11 (with XAML tabs), Windows 10,
    Explorer List/Grid/Icon/Details views, Desktop, Network Shares (UNC), Local FTP servers, and File Dialogs.
    """
    file_hovered = pyqtSignal(str, int, int) # (file_path, screen_x, screen_y)
    hover_cleared = pyqtSignal()
    space_pin_requested = pyqtSignal()
    escape_requested = pyqtSignal()
    toggle_enabled_requested = pyqtSignal() # Emitted on Ctrl+` global hotkey

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.enabled = config.get("enabled", True)
        self.hover_delay_ms = config.get("hover_delay_ms", 120)
        self.supported_exts = [ext.lower() for ext in config.get("supported_formats", SUPPORTED_EXTENSIONS.keys())]
        self.supported_exts_set = set(self.supported_exts)
        
        self.last_pos = QPoint(-1, -1)
        self.settle_start_time = 0
        self.is_hover_active = False
        self.preview_is_visible = False
        self.preview_is_pinned = False
        self.active_file_path = ""
        self.active_rect = None
        self._last_resolved_pos = QPoint(-1, -1)
        self.space_key_down = False
        self.esc_key_down = False
        self.ctrl_backtick_down = False
        
        # Desktop candidate folders
        self.desktop_paths = [
            os.path.normpath(os.path.expanduser("~/Desktop")),
            os.path.normpath(os.path.expanduser("~/OneDrive/Desktop")),
            os.path.normpath("C:/Users/Public/Desktop")
        ]

        # Timer ticks every 35ms for instant settle detection
        self.timer = QTimer(self)
        self.timer.setInterval(35)
        self.timer.timeout.connect(self._on_tick)

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self._clear_hover()

    def update_config(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.hover_delay_ms = config.get("hover_delay_ms", 120)
        self.supported_exts = [ext.lower() for ext in config.get("supported_formats", SUPPORTED_EXTENSIONS.keys())]
        self.supported_exts_set = set(self.supported_exts)

    def set_preview_visible(self, visible: bool):
        self.preview_is_visible = visible
        if not visible:
            self.space_key_down = False
            self.esc_key_down = False

    def set_preview_pinned(self, pinned: bool):
        self.preview_is_pinned = pinned

    def _on_tick(self):
        # Global Key Interceptions when preview is active or visible or pinned
        if self.is_hover_active or self.preview_is_visible or self.preview_is_pinned:
            # Spacebar detection (0x20 = VK_SPACE)
            space_state = bool(win32api.GetAsyncKeyState(win32con.VK_SPACE) & 0x8000)
            if space_state and not self.space_key_down:
                self.space_key_down = True
                self.space_pin_requested.emit()
            elif not space_state:
                self.space_key_down = False

            # Escape detection (0x1B = VK_ESCAPE)
            esc_state = bool(win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000)
            if esc_state and not self.esc_key_down:
                self.esc_key_down = True
                self.escape_requested.emit()
                self._clear_hover()
                return
            elif not esc_state:
                self.esc_key_down = False

        # Ctrl+` global hotkey: toggle hover preview ON/OFF (works system-wide, always)
        # VK_CONTROL = 0x11, VK_OEM_3 = 0xC0 (backtick/grave accent key)
        ctrl_state = bool(win32api.GetAsyncKeyState(0x11) & 0x8000)
        backtick_state = bool(win32api.GetAsyncKeyState(0xC0) & 0x8000)
        if ctrl_state and backtick_state and not self.ctrl_backtick_down:
            self.ctrl_backtick_down = True
            self.toggle_enabled_requested.emit()
        elif not (ctrl_state and backtick_state):
            self.ctrl_backtick_down = False

        if not self.enabled:
            if self.is_hover_active:
                self._clear_hover()
            return

        cur_pos = QCursor.pos()
        x, y = cur_pos.x(), cur_pos.y()
        now = ctypes.windll.kernel32.GetTickCount()

        if cur_pos != self.last_pos:
            # Cursor is in motion
            self.last_pos = cur_pos
            self.settle_start_time = now
            self._last_resolved_pos = QPoint(-1, -1)

            if self.preview_is_pinned:
                # Keep preview active when pinned
                return

            if self.is_hover_active and self.active_rect:
                left, top, right, bottom = self.active_rect
                # Tight vertical buffer (4px) so moving between adjacent rows triggers instant hover switch
                if x < left - 16 or x > right + 16 or y < top - 4 or y > bottom + 4:
                    self._clear_hover()
            return

        # Cursor is settled/dwelling: resolve once per settled position
        dwell_ms = now - self.settle_start_time
        if dwell_ms >= self.hover_delay_ms:
            if cur_pos != getattr(self, "_last_resolved_pos", QPoint(-1, -1)):
                self._last_resolved_pos = cur_pos
                self._resolve_and_trigger_hover(x, y)

    def _clear_hover(self):
        self.is_hover_active = False
        self.active_file_path = ""
        self.active_rect = None
        self._last_resolved_pos = QPoint(-1, -1)
        self.hover_cleared.emit()

    def _resolve_and_trigger_hover(self, x: int, y: int):
        file_path, bounding_rect = self._resolve_file_from_point(x, y)
        if file_path:
            is_valid = file_path.startswith("ftp://") or file_path.startswith("ftps://") or os.path.isfile(file_path)
            if is_valid:
                ext = Path(file_path).suffix.lower()
                if ext in self.supported_exts_set:
                    # Emit if path changed OR if bounding rect moved to a new row/item
                    rect_changed = False
                    if self.active_rect and bounding_rect:
                        # Check if row vertically changed by more than 10px
                        if abs(self.active_rect[1] - bounding_rect[1]) > 8:
                            rect_changed = True

                    if self.active_file_path != file_path or rect_changed:
                        self.active_file_path = file_path
                        self.active_rect = bounding_rect
                        self.is_hover_active = True
                        self.file_hovered.emit(file_path, x, y)
                    return
        
        # If not hovering over a valid file and we were active
        if self.is_hover_active and not self.preview_is_pinned:
            if self.active_rect:
                left, top, right, bottom = self.active_rect
                if x < left - 16 or x > right + 16 or y < top - 4 or y > bottom + 4:
                    self._clear_hover()
            else:
                self._clear_hover()

    def _get_active_explorer_context(self, x: int, y: int, expected_folder_name: str = "") -> tuple[str, list[str], list[str], list[str]]:
        """
        Queries the exact Shell window/tab under the mouse cursor.
        Gathers folder paths and items from all tabs belonging to the Explorer window.
        Returns (active_folder, focused_paths, selected_paths, tab_folders).
        """
        active_folder = ""
        focused_paths = []
        selected_paths = []
        tab_folders = []
        try:
            hwnd = win32gui.WindowFromPoint((x, y))
            if not hwnd:
                return "", [], [], []
            
            root_hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
            
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("Shell.Application")
            
            matching_windows = []
            for w in shell.Windows():
                try:
                    w_hwnd = getattr(w, "HWND", 0)
                    if w_hwnd == root_hwnd or w_hwnd == hwnd:
                        matching_windows.append(w)
                except Exception:
                    continue

            clean_expected = expected_folder_name.strip().lower() if expected_folder_name else ""
            target_w = None

            for w in matching_windows:
                try:
                    url = str(getattr(w, "LocationURL", ""))
                    doc_path = ""
                    if hasattr(w, "Document") and hasattr(w.Document, "Folder"):
                        doc_path = str(w.Document.Folder.Self.Path)
                    
                    p_folder = parse_shell_url(url) or parse_shell_url(doc_path)
                    if p_folder and (p_folder.startswith("ftp://") or p_folder.startswith("ftps://") or os.path.isdir(p_folder)):
                        if p_folder not in tab_folders:
                            tab_folders.append(p_folder)
                    
                    loc_name = str(getattr(w, "LocationName", "")).strip().lower()
                    loc_url = p_folder.lower()
                    if clean_expected and (loc_name == clean_expected or loc_url.endswith(clean_expected) or clean_expected in loc_url):
                        target_w = w

                    if hasattr(w, "Document"):
                        doc = w.Document
                        try:
                            focused = getattr(doc, "FocusedItem", None)
                            if focused and hasattr(focused, "Path"):
                                f_p = str(focused.Path)
                                if f_p and f_p not in focused_paths:
                                    focused_paths.append(f_p)
                        except Exception:
                            pass
                        try:
                            sel = doc.SelectedItems()
                            if sel:
                                for i in range(min(sel.Count, 10)):
                                    s_item = sel.Item(i)
                                    if hasattr(s_item, "Path"):
                                        s_p = str(s_item.Path)
                                        if s_p and s_p not in selected_paths:
                                            selected_paths.append(s_p)
                        except Exception:
                            pass
                except Exception:
                    continue

            if target_w:
                url = str(getattr(target_w, "LocationURL", ""))
                doc_path = ""
                if hasattr(target_w, "Document") and hasattr(target_w.Document, "Folder"):
                    doc_path = str(target_w.Document.Folder.Self.Path)
                active_folder = parse_shell_url(url) or parse_shell_url(doc_path)
            elif tab_folders:
                active_folder = tab_folders[0]

        except Exception:
            pass
        return active_folder, focused_paths, selected_paths, tab_folders

    def _get_candidate_folders(self, priority_folder: str = "", tab_folders: list = None, is_explorer_window: bool = False, is_desktop: bool = False) -> list:
        """Retrieves active folder paths scoped strictly to the hovered window/tab context."""
        folders = []
        if priority_folder and (priority_folder.startswith("ftp://") or priority_folder.startswith("ftps://") or os.path.isdir(priority_folder)):
            folders.append(priority_folder)

        if tab_folders:
            for tf in tab_folders:
                if tf not in folders:
                    folders.append(tf)

        # If hovering over Desktop, only search desktop locations
        if is_desktop:
            for dp in self.desktop_paths:
                if dp not in folders and os.path.isdir(dp):
                    folders.append(dp)
            return folders

        # If hovering inside an Explorer window and active tabs were found, restrict search ONLY to this window
        if is_explorer_window and folders:
            return folders

        # Fallback only when window is unknown/undetermined
        try:
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("Shell.Application")
            for w in shell.Windows():
                try:
                    url = str(getattr(w, "LocationURL", ""))
                    doc_path = ""
                    if hasattr(w, "Document") and hasattr(w.Document, "Folder"):
                        doc_path = str(w.Document.Folder.Self.Path)
                    
                    parsed = parse_shell_url(url) or parse_shell_url(doc_path)
                    if parsed and (parsed.startswith("ftp://") or parsed.startswith("ftps://") or os.path.isdir(parsed)) and parsed not in folders:
                        folders.append(parsed)
                except Exception:
                    continue
        except Exception:
            pass

        for dp in self.desktop_paths:
            if dp not in folders and os.path.isdir(dp):
                folders.append(dp)

        return folders

    def _resolve_file_from_point(self, x: int, y: int):
        try:
            elem = auto.ControlFromPoint(x, y)
            if not elem:
                return None, None

            bounding_box = None
            try:
                r = elem.BoundingRectangle
                if r:
                    bounding_box = (r.left, r.top, r.right, r.bottom)
            except Exception:
                pass

            # Ascend to find the row container (ListItem, DataItem, TreeItem)
            row_control = None
            curr = elem
            depth = 0
            while curr and depth < 8:
                if curr.ControlTypeName in ("ListItemControl", "DataItemControl", "TreeItemControl"):
                    row_control = curr
                    try:
                        row_r = curr.BoundingRectangle
                        if row_r:
                            bounding_box = (row_r.left, row_r.top, row_r.right, row_r.bottom)
                    except Exception:
                        pass
                    break

                if curr.ControlTypeName in ("WindowControl", "DesktopControl"):
                    break
                
                curr = curr.GetParentControl()
                depth += 1

            # If no row container was found
            if not row_control:
                # If hovering over blank list canvas / pane / toolbar / scrollbar, ignore
                if elem.ControlTypeName in ("ListControl", "PaneControl", "WindowControl", "ScrollBarControl", "HeaderControl", "HeaderItemControl", "ToolBarControl", "MenuBarControl", "GroupControl"):
                    return None, None
                row_control = elem

            # Identify window type
            hwnd = win32gui.WindowFromPoint((x, y))
            root_hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT) if hwnd else 0
            cls_name = win32gui.GetClassName(root_hwnd) if root_hwnd else ""
            is_explorer_window = (cls_name == "CabinetWClass")
            is_desktop = (cls_name in ("Progman", "WorkerW"))

            # Find parent list container name (e.g. "Downloads", "Space", etc.)
            folder_hint = ""
            p = row_control.GetParentControl()
            p_depth = 0
            while p and p_depth < 6:
                if p.Name and p.ControlTypeName in ("ListControl", "TreeControl", "PaneControl", "WindowControl"):
                    folder_hint = p.Name
                    break
                p = p.GetParentControl()
                p_depth += 1

            # 1. Query active Explorer COM context under cursor for this specific window and all its tabs
            priority_folder, focused_paths, selected_paths, tab_folders = self._get_active_explorer_context(x, y, expected_folder_name=folder_hint)
            candidate_folders = self._get_candidate_folders(priority_folder, tab_folders, is_explorer_window=is_explorer_window, is_desktop=is_desktop)

            # 2. Extract Name & attributes strictly from the item row and its children
            names_to_try = []
            type_hints = []
            size_hints = []

            def is_valid_name(s: str) -> bool:
                if not s or "\n" in s or "\r" in s:
                    return False
                lower = s.lower().strip()
                if any(lower.startswith(k) for k in ("item type:", "type:", "size:", "date modified:", "dimensions:", "rating:")):
                    return False
                return True

            if elem != row_control and is_valid_name(elem.Name):
                names_to_try.append(elem.Name.strip())
            if is_valid_name(row_control.Name):
                names_to_try.append(row_control.Name.strip())

            row_help = getattr(row_control, 'HelpText', '')
            if row_help:
                type_hints.append(row_help)
                size_hints.append(row_help)
            row_item_type = getattr(row_control, 'ItemType', '')
            if row_item_type:
                type_hints.append(row_item_type)

            # Inspect child columns
            try:
                for child in row_control.GetChildren():
                    c_name = child.Name
                    c_auto_id = getattr(child, "AutomationId", "")
                    c_help = getattr(child, "HelpText", "")
                    c_type = getattr(child, "ItemType", "")

                    if c_name:
                        if c_auto_id == "System.ItemNameDisplay" and is_valid_name(c_name):
                            names_to_try.append(c_name.strip())
                        elif is_valid_name(c_name) and not any(k in c_name.lower() for k in ("kb", "mb", "gb", "document", "image", "file", "format")):
                            names_to_try.append(c_name.strip())

                        if any(k in c_name.lower() for k in ("document", "image", "file", "format", "postscript", "pdf", "artwork", "tiff", "raw", "photoshop", "illustrator")):
                            type_hints.append(c_name)
                        if any(k in c_name.lower() for k in ("kb", "mb", "gb", "bytes", "b")) and re.search(r"\d", c_name):
                            size_hints.append(c_name)
                    
                    if c_auto_id == "System.ItemTypeText" and c_name:
                        type_hints.append(c_name)
                    elif c_auto_id == "System.Size" and c_name:
                        size_hints.append(c_name)

                    if c_help:
                        type_hints.append(c_help)
                        size_hints.append(c_help)
                    if c_type:
                        type_hints.append(c_type)
            except Exception:
                pass

            if not names_to_try:
                return None, None

            # 3. Explicit File Extension Check:
            # If the item name already has an explicit extension (e.g. "Kids.jpg", "Archive.zip"),
            # and that extension is NOT enabled in settings, immediately abort! Never guess other extensions!
            for raw_n in names_to_try:
                n_ext = Path(raw_n).suffix.lower()
                if n_ext and len(n_ext) in range(2, 7) and not n_ext[1:].isdigit():
                    if n_ext not in self.supported_exts_set:
                        return None, None

            # 4. Type Hint Detection & Strict Abort for Disabled Formats:
            inferred_exts = []
            for th in type_hints:
                for e in detect_extensions_from_type_text(th):
                    if e not in inferred_exts:
                        inferred_exts.append(e)

            target_exts = []
            if inferred_exts:
                supported_inferred = [e for e in inferred_exts if e in self.supported_exts_set]
                if not supported_inferred:
                    # Item is definitely of a disabled or unsupported format (e.g. JPG when basic images is disabled).
                    # Do NOT fall back to guessing .psd or other formats!
                    return None, None
                target_exts = supported_inferred

            # Parse size hint if available
            parsed_kb = None
            for sh in size_hints:
                val = parse_size_in_kb(sh)
                if val is not None:
                    parsed_kb = val
                    break

            # 5. Check COM focused/selected items strictly within candidate folders
            all_com_cands = focused_paths + selected_paths
            for com_path in all_com_cands:
                if com_path and os.path.isfile(com_path):
                    # Ensure COM item actually belongs to the hovered folder/tabs
                    if not any(Path(com_path).parent == Path(cf) for cf in candidate_folders):
                        continue
                    com_ext = Path(com_path).suffix.lower()
                    if com_ext in self.supported_exts_set:
                        if target_exts and com_ext not in target_exts:
                            continue
                        com_stem = Path(com_path).stem.lower()
                        com_name = Path(com_path).name.lower()
                        for raw_name in names_to_try:
                            clean_n = raw_name.strip().lower()
                            if clean_n in (com_stem, com_name) or normalize_str(clean_n) in (normalize_str(com_stem), normalize_str(com_name)):
                                return com_path, bounding_box

            # 6. Search candidate folders with Stem Collision Disambiguation
            for raw_name in names_to_try:
                clean_name = " ".join(raw_name.split())
                if not clean_name:
                    continue
                norm_name = normalize_str(clean_name)

                for folder in candidate_folders:
                    # FTP candidate check
                    if folder.startswith("ftp://") or folder.startswith("ftps://"):
                        ext = Path(clean_name).suffix.lower()
                        if ext in self.supported_exts_set:
                            return f"{folder.rstrip('/')}/{clean_name}", bounding_box
                        search_order = target_exts if target_exts else self.supported_exts
                        for e in search_order:
                            return f"{folder.rstrip('/')}/{clean_name}{e}", bounding_box
                        continue

                    if not os.path.isdir(folder):
                        continue

                    # Direct match if clean_name already includes a supported extension
                    ext = Path(clean_name).suffix.lower()
                    if ext in self.supported_exts_set:
                        direct_p = os.path.join(folder, clean_name)
                        if os.path.isfile(direct_p):
                            return direct_p, bounding_box

                    # Find ALL files on disk in this folder matching this stem
                    matching_disk_files = []
                    try:
                        for f in os.listdir(folder):
                            f_path = os.path.join(folder, f)
                            if os.path.isfile(f_path):
                                f_stem = Path(f).stem
                                if f_stem.lower() == clean_name.lower() or normalize_str(f_stem) == norm_name or f.lower() == clean_name.lower():
                                    matching_disk_files.append(f_path)
                    except Exception:
                        continue

                    if not matching_disk_files:
                        continue

                    # CASE 1: Exactly one file on disk matches this name
                    if len(matching_disk_files) == 1:
                        single_p = matching_disk_files[0]
                        single_ext = Path(single_p).suffix.lower()
                        if single_ext in self.supported_exts_set:
                            return single_p, bounding_box
                        else:
                            # The file exists in the active folder, but its format is disabled/unsupported.
                            # Never search other folders!
                            return None, None

                    # CASE 2: Multiple files on disk match this base name (Stem Collision e.g. .psd and .jpg)
                    # A. Type hint disambiguation
                    if target_exts:
                        type_matched = [p for p in matching_disk_files if Path(p).suffix.lower() in target_exts]
                        if type_matched:
                            if len(type_matched) == 1:
                                return type_matched[0], bounding_box
                            if parsed_kb is not None:
                                best = min(type_matched, key=lambda p: abs(os.path.getsize(p)/1024.0 - parsed_kb))
                                return best, bounding_box
                            return type_matched[0], bounding_box

                    # B. Size hint disambiguation
                    if parsed_kb is not None:
                        best_p = min(matching_disk_files, key=lambda p: abs(os.path.getsize(p)/1024.0 - parsed_kb))
                        best_diff = abs(os.path.getsize(best_p)/1024.0 - parsed_kb)
                        if best_diff < max(parsed_kb * 0.40, 250):
                            if Path(best_p).suffix.lower() in self.supported_exts_set:
                                return best_p, bounding_box
                            else:
                                # The hovered item matches a disabled file (e.g. 203 KB JPG instead of 93 MB PSD)
                                return None, None

                    # C. COM Focused / Selected item match
                    com_matches = [p for p in matching_disk_files if p in all_com_cands]
                    if com_matches:
                        com_p = com_matches[0]
                        if Path(com_p).suffix.lower() in self.supported_exts_set:
                            return com_p, bounding_box
                        else:
                            return None, None

                    # D. If still ambiguous and some files are unsupported/disabled:
                    # NEVER blindly return a supported file if an unsupported file also shares the stem!
                    has_unsupported = any(Path(p).suffix.lower() not in self.supported_exts_set for p in matching_disk_files)
                    if has_unsupported:
                        return None, None

                    # If all matching files are supported, pick the first
                    supported_only = [p for p in matching_disk_files if Path(p).suffix.lower() in self.supported_exts_set]
                    if supported_only:
                        return supported_only[0], bounding_box

        except Exception:
            pass

        return None, None

