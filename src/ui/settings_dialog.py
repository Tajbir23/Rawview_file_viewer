import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox,
    QPushButton, QGroupBox, QGridLayout, QMessageBox, QScrollArea, QWidget,
    QLineEdit, QApplication, QTabWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QColor, QPalette, QDesktopServices
from src.core.config import (
    save_config, SUPPORTED_EXTENSIONS, CACHE_DIR, APP_NAME, APP_VERSION, PAYMENT_INFO
)
from src.core.autostart import set_autostart, is_autostart_enabled
from src.core.licensing import get_license_status, activate_license, get_machine_id

class SettingsDialog(QDialog):
    """Modern dark-themed tabbed preferences dialog for RawView v3.9.1."""
    config_changed = pyqtSignal(dict)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} - Settings & Controls")
        self.setFixedSize(620, 780)
        self._init_style()
        self._init_ui()

    def _init_style(self):
        assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
        checkmark_svg = (assets_dir / "checkmark.svg").as_posix()

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #0B0E17;
                color: #E2E8F0;
                font-family: 'Segoe UI', sans-serif;
            }}
            QTabWidget::pane {{
                border: 1px solid #1E293B;
                border-radius: 8px;
                background-color: #0B0E17;
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: #111625;
                color: #94A3B8;
                border: 1px solid #1E293B;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 9px 20px;
                margin-right: 4px;
                font-weight: 600;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background-color: #0B0E17;
                color: #38BDF8;
                border-color: #38BDF8;
                border-bottom: 2px solid #0B0E17;
                font-weight: 700;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #1E293B;
                color: #E2E8F0;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #0B0E17;
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #334155;
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #475569;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QGroupBox {{
                border: 1px solid #1E293B;
                border-radius: 10px;
                margin-top: 14px;
                padding-top: 12px;
                font-weight: 700;
                font-size: 12px;
                color: #38BDF8;
                background-color: #111625;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }}
            QLabel {{
                font-size: 12px;
                color: #CBD5E1;
            }}
            QLineEdit {{
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #F8FAFC;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: #38BDF8;
            }}
            QCheckBox {{
                font-size: 12px;
                color: #E2E8F0;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid #475569;
                border-radius: 4px;
                background-color: #1E293B;
            }}
            QCheckBox::indicator:hover {{
                border-color: #38BDF8;
            }}
            QCheckBox::indicator:checked {{
                background-color: #0284C7;
                border-color: #38BDF8;
                image: url({checkmark_svg});
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: #0369A1;
                border-color: #38BDF8;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: #1E293B;
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: #38BDF8;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: #FFFFFF;
                border: 2px solid #38BDF8;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }}
            QPushButton {{
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #334155;
                border-color: #64748B;
            }}
            QPushButton#saveBtn {{
                background-color: #0284C7;
                border: 1px solid #38BDF8;
                color: #FFFFFF;
            }}
            QPushButton#saveBtn:hover {{
                background-color: #0369A1;
            }}
            QPushButton#activateBtn {{
                background-color: #059669;
                border: 1px solid #10B981;
                color: #FFFFFF;
                font-weight: 700;
            }}
            QPushButton#activateBtn:hover {{
                background-color: #047857;
            }}
            QPushButton#copyBkashBtn {{
                background-color: #E11D48;
                border: 1px solid #F43F5E;
                color: #FFFFFF;
                font-weight: 600;
            }}
            QPushButton#copyBkashBtn:hover {{
                background-color: #BE123C;
            }}
            QPushButton#waBtn {{
                background-color: #059669;
                border: 1px solid #34D399;
                color: #FFFFFF;
                font-weight: 600;
            }}
            QPushButton#waBtn:hover {{
                background-color: #047857;
            }}
        """)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        # Tab Widget Header
        self.tabs = QTabWidget(self)

        # Tab 1: Preferences
        pref_tab = self._create_preferences_tab()
        self.tabs.addTab(pref_tab, "⚙️ Preferences")

        # Tab 2: Shortcuts & Controls (using && so & is not consumed as mnemonic)
        shortcuts_tab = self._create_shortcuts_tab()
        self.tabs.addTab(shortcuts_tab, "⌨️ Shortcuts && Controls")

        root_layout.addWidget(self.tabs, stretch=1)

        # Action Buttons pinned at bottom
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 4, 4, 0)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save && Apply", self)
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save_and_apply)
        btn_layout.addWidget(save_btn)

        root_layout.addLayout(btn_layout)

    def _create_preferences_tab(self) -> QWidget:
        """Constructs the scrollable preferences and configuration tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(scroll_widget)
        main_layout.setContentsMargins(4, 6, 12, 6)
        main_layout.setSpacing(12)

        # 1. Pro License & Activation Section
        lic_group = QGroupBox("RawView Pro License (50 TK Lifetime)", self)
        lic_layout = QVBoxLayout(lic_group)
        lic_layout.setContentsMargins(14, 12, 14, 12)
        lic_layout.setSpacing(8)

        lic_info = get_license_status()

        # Status Header Row
        status_row = QHBoxLayout()
        status_label_title = QLabel("Status:")
        status_label_title.setStyleSheet("font-weight: 600;")
        status_row.addWidget(status_label_title)

        self.status_badge = QLabel(self)
        self.status_badge.setStyleSheet("padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 11px;")
        status_row.addWidget(self.status_badge)
        status_row.addStretch()
        lic_layout.addLayout(status_row)

        # Machine ID Row
        mid_row = QHBoxLayout()
        mid_label = QLabel("1. Machine Code:")
        mid_label.setStyleSheet("font-weight: 600;")
        self.mid_val = QLineEdit(lic_info.get("machine_id", get_machine_id()))
        self.mid_val.setReadOnly(True)
        self.mid_val.setStyleSheet("color: #38BDF8; font-weight: bold; font-family: monospace;")
        copy_mid_btn = QPushButton("📋 Copy Code")
        copy_mid_btn.clicked.connect(self._copy_machine_id)
        mid_row.addWidget(mid_label)
        mid_row.addWidget(self.mid_val, stretch=1)
        mid_row.addWidget(copy_mid_btn)
        lic_layout.addLayout(mid_row)

        # bKash Payment Row
        self.bkash_row_widget = QWidget()
        bkash_row = QHBoxLayout(self.bkash_row_widget)
        bkash_row.setContentsMargins(0, 0, 0, 0)
        bkash_label = QLabel("2. bKash Personal (50 TK):")
        bkash_label.setStyleSheet("color: #FB7185; font-weight: 700;")
        self.bkash_val = QLineEdit(PAYMENT_INFO.get("bkash_number", "01756678087"))
        self.bkash_val.setReadOnly(True)
        self.bkash_val.setStyleSheet("color: #FFFFFF; font-weight: bold; font-family: monospace; border: 1px solid #E11D48;")
        copy_bkash_btn = QPushButton("📋 Copy bKash")
        copy_bkash_btn.setObjectName("copyBkashBtn")
        copy_bkash_btn.clicked.connect(self._copy_bkash)
        bkash_row.addWidget(bkash_label)
        bkash_row.addWidget(self.bkash_val, stretch=1)
        bkash_row.addWidget(copy_bkash_btn)
        lic_layout.addWidget(self.bkash_row_widget)

        # WhatsApp Support Row
        self.wa_row_widget = QWidget()
        wa_row = QHBoxLayout(self.wa_row_widget)
        wa_row.setContentsMargins(0, 0, 0, 0)
        wa_label = QLabel("3. WhatsApp Support:")
        wa_label.setStyleSheet("color: #34D399; font-weight: 700;")
        self.wa_val = QLineEdit(PAYMENT_INFO.get("whatsapp_number", "+1 (202) 780-6050"))
        self.wa_val.setReadOnly(True)
        self.wa_val.setStyleSheet("color: #FFFFFF; font-weight: 600; border: 1px solid #10B981;")
        wa_btn = QPushButton("💬 Open WhatsApp")
        wa_btn.setObjectName("waBtn")
        wa_btn.clicked.connect(self._open_whatsapp)
        wa_row.addWidget(wa_label)
        wa_row.addWidget(self.wa_val, stretch=1)
        wa_row.addWidget(wa_btn)
        lic_layout.addWidget(self.wa_row_widget)

        # License Key Input Row (Active if not Pro)
        self.key_input_layout = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("4. Enter License Key (e.g. RVPRO-XXXX-XXXX-XXXX)...")
        self.activate_btn = QPushButton("⚡ Activate Pro")
        self.activate_btn.setObjectName("activateBtn")
        self.activate_btn.clicked.connect(self._do_activate_license)
        self.key_input_layout.addWidget(self.key_input, stretch=1)
        self.key_input_layout.addWidget(self.activate_btn)
        lic_layout.addLayout(self.key_input_layout)

        # Payment / Purchase instructions note
        self.pay_note = QLabel(
            "Send 50 TK via bKash Personal (Ref: Machine Code), send TrxID on WhatsApp to get your License Key."
        )
        self.pay_note.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.pay_note.setWordWrap(True)
        lic_layout.addWidget(self.pay_note)

        self._refresh_license_ui()
        main_layout.addWidget(lic_group)

        # 2. General Settings
        gen_group = QGroupBox("General Preferences", self)
        gen_layout = QVBoxLayout(gen_group)
        gen_layout.setContentsMargins(14, 12, 14, 10)
        gen_layout.setSpacing(8)

        self.enable_cb = QCheckBox("Enable Mouse Hover Previews", self)
        self.enable_cb.setChecked(self.config.get("enabled", True))
        gen_layout.addWidget(self.enable_cb)

        self.autostart_cb = QCheckBox("Start RawView automatically on Windows boot", self)
        self.autostart_cb.setChecked(is_autostart_enabled())
        gen_layout.addWidget(self.autostart_cb)

        main_layout.addWidget(gen_group)

        # 3. Timing & Performance
        perf_group = QGroupBox("Hover Responsiveness", self)
        perf_layout = QVBoxLayout(perf_group)
        perf_layout.setContentsMargins(14, 12, 14, 10)
        perf_layout.setSpacing(6)

        slider_header = QHBoxLayout()
        slider_label = QLabel("Hover Settle Delay:")
        self.delay_val_label = QLabel(f"{self.config.get('hover_delay_ms', 120)} ms")
        self.delay_val_label.setStyleSheet("color: #38BDF8; font-weight: bold;")
        slider_header.addWidget(slider_label)
        slider_header.addStretch()
        slider_header.addWidget(self.delay_val_label)
        perf_layout.addLayout(slider_header)

        self.delay_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.delay_slider.setRange(40, 350)
        self.delay_slider.setSingleStep(10)
        self.delay_slider.setValue(self.config.get("hover_delay_ms", 120))
        self.delay_slider.valueChanged.connect(lambda val: self.delay_val_label.setText(f"{val} ms"))
        perf_layout.addWidget(self.delay_slider)

        main_layout.addWidget(perf_group)

        # 4. Graphics & Vector Formats
        gfx_group = QGroupBox("Graphics && Design Formats", self)
        gfx_layout = QGridLayout(gfx_group)
        gfx_layout.setContentsMargins(14, 12, 14, 10)
        gfx_layout.setHorizontalSpacing(20)
        gfx_layout.setVerticalSpacing(6)

        self.format_cbs = {}
        active_fmts = set(self.config.get("supported_formats", SUPPORTED_EXTENSIONS.keys()))

        gfx_items = [
            (".psd", "PSD (Adobe Photoshop)"),
            (".psb", "PSB (Large Document)"),
            (".ai",  "AI (Adobe Illustrator)"),
            (".eps", "EPS (PostScript Vector)"),
            (".pdf", "PDF (Vector Document)"),
            (".tiff","TIFF (High-Res Image)"),
            (".svg", "SVG (Scalable Vector)"),
            (".dng", "RAW (Camera RAW Files)"),
        ]

        for idx, (ext, label) in enumerate(gfx_items):
            cb = QCheckBox(label, self)
            cb.setChecked(ext in active_fmts)
            self.format_cbs[ext] = cb
            row = idx // 2
            col = idx % 2
            gfx_layout.addWidget(cb, row, col)

        main_layout.addWidget(gfx_group)

        # 5. Microsoft Office & Documents
        office_group = QGroupBox("Microsoft Office && Documents", self)
        office_layout = QGridLayout(office_group)
        office_layout.setContentsMargins(14, 12, 14, 10)
        office_layout.setHorizontalSpacing(20)
        office_layout.setVerticalSpacing(6)

        office_items = [
            (".docx", "Word (.docx, .doc)"),
            (".xlsx", "Excel (.xlsx, .xls)"),
            (".pptx", "PowerPoint (.pptx, .ppt)"),
            (".rtf",  "Rich Text && CSV (.rtf, .csv)"),
        ]

        for idx, (ext, label) in enumerate(office_items):
            cb = QCheckBox(label, self)
            cb.setChecked(ext in active_fmts)
            self.format_cbs[ext] = cb
            row = idx // 2
            col = idx % 2
            office_layout.addWidget(cb, row, col)

        main_layout.addWidget(office_group)

        # 6. Adobe Video & Motion Projects
        adobe_group = QGroupBox("Adobe Video && Motion Projects", self)
        adobe_layout = QGridLayout(adobe_group)
        adobe_layout.setContentsMargins(14, 12, 14, 10)
        adobe_layout.setHorizontalSpacing(20)
        adobe_layout.setVerticalSpacing(6)

        adobe_items = [
            (".aep", "After Effects (.aep, .aet)"),
            (".prproj", "Premiere Pro (.prproj, .prset)"),
        ]

        for idx, (ext, label) in enumerate(adobe_items):
            cb = QCheckBox(label, self)
            cb.setChecked(ext in active_fmts)
            self.format_cbs[ext] = cb
            row = idx // 2
            col = idx % 2
            adobe_layout.addWidget(cb, row, col)

        main_layout.addWidget(adobe_group)

        # 7. Live Video Formats
        vid_group = QGroupBox("Live Video Formats", self)
        vid_layout = QGridLayout(vid_group)
        vid_layout.setContentsMargins(14, 12, 14, 10)
        vid_layout.setHorizontalSpacing(20)
        vid_layout.setVerticalSpacing(6)

        vid_items = [
            (".mp4", "MP4 (MPEG-4 Video)"),
            (".mkv", "MKV (Matroska Video)"),
            (".mov", "MOV (QuickTime Movie)"),
            (".avi", "AVI (Audio Video)"),
            (".webm","WebM (Web Video)"),
            (".wmv", "WMV (Windows Media)"),
            (".flv", "FLV (Flash Video)"),
            (".ts",  "TS (MPEG Stream)"),
        ]

        for idx, (ext, label) in enumerate(vid_items):
            cb = QCheckBox(label, self)
            cb.setChecked(ext in active_fmts)
            self.format_cbs[ext] = cb
            row = idx // 2
            col = idx % 2
            vid_layout.addWidget(cb, row, col)

        main_layout.addWidget(vid_group)

        # 8. Standard & Web Images (Disabled by default)
        std_group = QGroupBox("Standard && Web Images (Off by default - Check to enable)", self)
        std_layout = QGridLayout(std_group)
        std_layout.setContentsMargins(14, 12, 14, 10)
        std_layout.setHorizontalSpacing(20)
        std_layout.setVerticalSpacing(6)

        std_items = [
            (".jpg", "JPEG / JPG (.jpg, .jpeg)"),
            (".png", "PNG (Portable Network Graphics)"),
            (".webp", "WebP (Google Web Image)"),
            (".gif", "GIF (Interchange / Animation)"),
            (".ico", "ICO (Windows Icon Format)"),
            (".bmp", "BMP (Standard Windows Bitmap)"),
        ]

        for idx, (ext, label) in enumerate(std_items):
            cb = QCheckBox(label, self)
            cb.setChecked(ext in active_fmts)
            self.format_cbs[ext] = cb
            row = idx // 2
            col = idx % 2
            std_layout.addWidget(cb, row, col)

        main_layout.addWidget(std_group)

        # 9. Cache Management
        cache_group = QGroupBox("Cache && Storage")
        cache_layout = QHBoxLayout(cache_group)
        cache_layout.setContentsMargins(14, 10, 14, 10)

        cache_size_mb = self._get_cache_size_mb()
        self.cache_info_label = QLabel(f"Thumbnail Cache: {cache_size_mb:.1f} MB")
        cache_layout.addWidget(self.cache_info_label)
        cache_layout.addStretch()

        clear_btn = QPushButton("Clear Cache")
        clear_btn.clicked.connect(self._clear_cache)
        cache_layout.addWidget(clear_btn)
        main_layout.addWidget(cache_group)

        # 10. Software Updates
        update_group = QGroupBox("Software Updates")
        update_layout = QVBoxLayout(update_group)
        update_layout.setContentsMargins(14, 12, 14, 12)
        update_layout.setSpacing(8)

        self.auto_update_cb = QCheckBox("Automatically check for updates weekly (via GitHub Releases)")
        self.auto_update_cb.setChecked(self.config.get("auto_check_updates", True))
        update_layout.addWidget(self.auto_update_cb)

        up_action_layout = QHBoxLayout()
        self.check_updates_btn = QPushButton("🔄 Check for Updates Now")
        self.check_updates_btn.setObjectName("checkUpdatesBtn")
        self.check_updates_btn.clicked.connect(self._on_check_updates_clicked)
        up_action_layout.addWidget(self.check_updates_btn)

        last_ts = self.config.get("last_update_check_timestamp", 0.0)
        if last_ts > 0:
            import datetime
            dt_str = datetime.datetime.fromtimestamp(last_ts).strftime("%d %b %Y, %I:%M %p")
            status_init = f"Last checked: {dt_str} | Current version: {APP_VERSION}"
        else:
            status_init = f"Current version: {APP_VERSION} | Never checked"

        self.update_status_label = QLabel(status_init)
        self.update_status_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        up_action_layout.addWidget(self.update_status_label, stretch=1)

        update_layout.addLayout(up_action_layout)
        main_layout.addWidget(update_group)

        scroll.setWidget(scroll_widget)
        return scroll

    def _create_shortcuts_tab(self) -> QWidget:
        """Constructs the visual reference guide explaining all shortcuts and controls."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(6, 10, 14, 10)
        layout.setSpacing(10)

        # Top Banner
        tip_frame = QFrame()
        tip_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(56, 189, 248, 0.08);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        tip_layout = QHBoxLayout(tip_frame)
        tip_layout.setContentsMargins(8, 4, 8, 4)
        tip_lbl = QLabel(
            "<b>💡 Pro Tip:</b> Press <b>Space</b> while hovering over any file to pin the preview window! "
            "Once pinned, you can freely zoom, pan, or copy artwork without the window closing."
        )
        tip_lbl.setWordWrap(True)
        tip_lbl.setStyleSheet("color: #38BDF8; font-size: 12px;")
        tip_layout.addWidget(tip_lbl)
        layout.addWidget(tip_frame)

        # 9 Interactive Shortcuts & Controls
        shortcuts_data = [
            (
                "Ctrl + `",
                "Toggle Preview Service",
                "System-wide global hotkey to turn RawView hover previews <b>On or Off</b> anywhere in Windows without opening settings.",
                "System Hotkey"
            ),
            (
                "Space",
                "Pin Preview / Play & Pause Video",
                "<b>Image / Doc:</b> Freezes and pins the floating window on screen so you can interact with it.<br><b>Video:</b> Instantly plays or pauses live looping video footage.",
                "Primary Control"
            ),
            (
                "Mouse Wheel (Scroll)",
                "Zoom In & Zoom Out",
                "Smoothly scale images, vectors, and documents from <b>50% up to 800%</b>. Rasterized from high-definition master buffer with zero pixelation.",
                "Canvas Viewport"
            ),
            (
                "Left-Click + Drag",
                "Pan Across Zoomed Canvas",
                "Click and drag anywhere on the canvas while zoomed in to freely explore details and inspect artwork.",
                "Canvas Viewport"
            ),
            (
                "Double-Click",
                "Reset Zoom & Position",
                "Instantly resets zoom factor back to <b>100% default fit</b> and centers the image in the preview window.",
                "Canvas Viewport"
            ),
            (
                "Ctrl + C",
                "Copy Preview to Clipboard",
                "Copies the full-resolution preview image straight to your Windows clipboard. Paste directly into Photoshop, Illustrator, Word, or chat!",
                "Quick Export"
            ),
            (
                "Ctrl + O  or  Enter",
                "Open in Default App",
                "Instantly launches the previewed file in its default registered Windows application (e.g. Adobe Suite, Office, VLC) and dismisses the preview.",
                "Launch"
            ),
            (
                "Esc",
                "Close / Dismiss Preview",
                "Immediately closes and hides the floating preview window and resets viewport state.",
                "Dismiss"
            ),
            (
                "Mouse Hover Away",
                "Auto-Dismiss on Exit",
                "When unpinned, moving your mouse cursor off the file item in File Explorer or Desktop automatically hides the preview with zero lag.",
                "Natural Flow"
            ),
        ]

        for keys, title, desc, tag in shortcuts_data:
            card = self._create_shortcut_card(keys, title, desc, tag)
            layout.addWidget(card)

        layout.addStretch()
        scroll.setWidget(scroll_widget)
        return scroll

    def _create_shortcut_card(self, key_text: str, title: str, description: str, tag: str = "") -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #111625;
                border: 1px solid #1E293B;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #38BDF8;
                background-color: #151C2E;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(5)

        header = QHBoxLayout()
        header.setSpacing(8)

        key_badge = QLabel(key_text)
        key_badge.setStyleSheet("""
            background-color: #1E293B;
            color: #38BDF8;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid #334155;
        """)
        header.addWidget(key_badge)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #F8FAFC; font-weight: 700; font-size: 13px;")
        header.addWidget(title_lbl)
        header.addStretch()

        if tag:
            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet("""
                background-color: rgba(56, 189, 248, 0.12);
                color: #38BDF8;
                font-size: 10px;
                font-weight: 600;
                padding: 2px 7px;
                border-radius: 4px;
                border: 1px solid rgba(56, 189, 248, 0.25);
            """)
            header.addWidget(tag_lbl)

        layout.addLayout(header)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        return card

    def _refresh_license_ui(self):
        lic_info = get_license_status()
        status = lic_info.get("status")

        if status == "PRO_ACTIVE":
            self.status_badge.setText("✨ LIFETIME PRO ACTIVATED")
            self.status_badge.setStyleSheet("background-color: #064E3B; color: #34D399; border: 1px solid #10B981; padding: 3px 8px; border-radius: 4px; font-weight: 700;")
            self.key_input.setVisible(False)
            self.activate_btn.setVisible(False)
            self.bkash_row_widget.setVisible(False)
            self.wa_row_widget.setVisible(False)
            self.pay_note.setText("Your copy of RawView is fully activated with Lifetime Pro access. Thank you!")
            self.pay_note.setStyleSheet("color: #34D399; font-size: 11px; font-weight: 600;")
        elif status == "TRIAL_ACTIVE":
            days = lic_info.get("days_left", 7)
            self.status_badge.setText(f"⏳ 7-DAY FREE TRIAL ({days} DAYS LEFT)")
            self.status_badge.setStyleSheet("background-color: #0C4A6E; color: #38BDF8; border: 1px solid #0284C7; padding: 3px 8px; border-radius: 4px; font-weight: 700;")
            self.key_input.setVisible(True)
            self.activate_btn.setVisible(True)
            self.bkash_row_widget.setVisible(True)
            self.wa_row_widget.setVisible(True)
        else:
            self.status_badge.setText("🔒 TRIAL EXPIRED (ACTIVATION REQUIRED)")
            self.status_badge.setStyleSheet("background-color: #4C0519; color: #FB7185; border: 1px solid #E11D48; padding: 3px 8px; border-radius: 4px; font-weight: 700;")
            self.key_input.setVisible(True)
            self.activate_btn.setVisible(True)
            self.bkash_row_widget.setVisible(True)
            self.wa_row_widget.setVisible(True)

    def _copy_machine_id(self):
        mid = self.mid_val.text()
        QApplication.clipboard().setText(mid)
        QMessageBox.information(self, "Copied", f"Machine Code '{mid}' copied to clipboard!\nSend this code to WhatsApp (+1 202 780-6050) after sending 50 TK.")

    def _copy_bkash(self):
        num = self.bkash_val.text()
        QApplication.clipboard().setText(num)
        QMessageBox.information(self, "Copied", f"bKash Personal Number '{num}' copied to clipboard!\nSend 50 TK (Send Money) with your Machine Code as Reference.")

    def _open_whatsapp(self):
        mid = self.mid_val.text()
        msg = f"Hello! I sent 50 TK for RawView Lifetime Pro.\nMy Machine Code: {mid}"
        url_str = f"https://wa.me/12027806050?text={msg.replace(' ', '%20').replace('\n', '%0A')}"
        QDesktopServices.openUrl(QUrl(url_str))

    def _do_activate_license(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Input Required", "Please enter the Pro License Key sent by the seller.")
            return

        success, msg = activate_license(key)
        if success:
            QMessageBox.information(self, "Congratulations!", msg)
            self._refresh_license_ui()
        else:
            QMessageBox.warning(self, "Activation Failed", msg)

    def _get_cache_size_mb(self) -> float:
        total = 0
        if CACHE_DIR.exists():
            for f in CACHE_DIR.glob("*"):
                if f.is_file():
                    total += f.stat().st_size
        return total / (1024.0 * 1024.0)

    def _clear_cache(self):
        try:
            for f in CACHE_DIR.glob("*"):
                if f.is_file():
                    f.unlink(missing_ok=True)
            self.cache_info_label.setText("Thumbnail Cache: 0.0 MB")
            QMessageBox.information(self, "Cache Cleared", "Thumbnail cache has been successfully wiped.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to clear cache: {e}")

    def _save_and_apply(self):
        self.config["enabled"] = self.enable_cb.isChecked()
        self.config["hover_delay_ms"] = self.delay_slider.value()

        # Update formats
        selected = []
        for ext, cb in self.format_cbs.items():
            if cb.isChecked():
                selected.append(ext)
                if ext == ".tiff":
                    selected.append(".tif")
                elif ext == ".svg":
                    selected.append(".svgz")
                elif ext == ".jpg":
                    selected.append(".jpeg")
                elif ext == ".docx":
                    selected.extend([".doc", ".docm", ".dotx", ".dot"])
                elif ext == ".xlsx":
                    selected.extend([".xls", ".xlsm", ".xlsb", ".xltx"])
                elif ext == ".pptx":
                    selected.extend([".ppt", ".pptm", ".ppsx", ".potx"])
                elif ext == ".rtf":
                    selected.append(".csv")
                elif ext == ".aep":
                    selected.extend([".aet", ".aepx"])
                elif ext == ".prproj":
                    selected.append(".prset")
                elif ext == ".mp4":
                    selected.extend([".m4v", ".mpg", ".mpeg"])
                elif ext == ".dng":
                    selected.extend([".cr2", ".cr3", ".crw", ".nef", ".nrw", ".arw", ".srf", ".sr2", ".raf", ".orf", ".ori", ".rw2", ".pef", ".ptx", ".3fr", ".fff", ".iiq", ".raw", ".x3f"])
        self.config["supported_formats"] = selected

        # Autostart
        autostart_wanted = self.autostart_cb.isChecked()
        self.config["autostart"] = autostart_wanted
        set_autostart(autostart_wanted)

        # Software Updates
        self.config["auto_check_updates"] = self.auto_update_cb.isChecked()

        save_config(self.config)
        self.config_changed.emit(self.config)
        self.accept()

    def _on_check_updates_clicked(self):
        self.check_updates_btn.setEnabled(False)
        self.check_updates_btn.setText("Checking...")
        self.update_status_label.setText("⏳ Checking GitHub for updates...")
        self.update_status_label.setStyleSheet("color: #38BDF8; font-size: 11px;")

        from src.core.updater import UpdateCheckWorker
        self._update_worker = UpdateCheckWorker(timeout=6.0, parent=self)
        self._update_worker.update_checked.connect(self._on_update_check_result)
        self._update_worker.check_failed.connect(self._on_update_check_failed)
        self._update_worker.start()

    def _on_update_check_result(self, info: dict):
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText("🔄 Check for Updates Now")
        import time
        self.config["last_update_check_timestamp"] = time.time()
        
        has_update = info.get("has_update", False)
        latest_ver = info.get("latest_version", APP_VERSION)
        if has_update:
            self.update_status_label.setText(f"🚀 New version {latest_ver} available!")
            self.update_status_label.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px;")
            from src.ui.update_dialog import UpdatePromptDialog
            dlg = UpdatePromptDialog(info, parent=self)
            dlg.exec()
        else:
            self.update_status_label.setText(f"✅ You're up to date! RawView {APP_VERSION} is the latest version.")
            self.update_status_label.setStyleSheet("color: #34D399; font-size: 11px;")

    def _on_update_check_failed(self, error_msg: str):
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText("🔄 Check for Updates Now")
        self.update_status_label.setText(f"⚠️ Could not check updates: {error_msg}")
        self.update_status_label.setStyleSheet("color: #FB7185; font-size: 11px;")
