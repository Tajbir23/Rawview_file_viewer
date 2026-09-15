import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QMessageBox, QApplication
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import pyqtSignal, QObject
from src.core.config import APP_NAME, APP_VERSION, save_config
from src.core.icons import create_app_icon
from src.ui.settings_dialog import SettingsDialog

class TrayManager(QObject):
    """Manages the Windows System Tray icon, notifications, and context menu."""
    config_updated = pyqtSignal(dict)
    quit_requested = pyqtSignal()

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.settings_dialog = None
        self._init_tray()

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.icon = create_app_icon(64)
        self.tray.setIcon(self.icon)
        self.tray.setToolTip(f"{APP_NAME} {APP_VERSION} - Zero-Lag File Hover Previewer")

        # Context Menu
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #0F121C;
                color: #F1F5F9;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0284C7;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #1E293B;
                margin: 4px 6px;
            }
        """)

        # 1. Header item
        header_action = QAction(f"{APP_NAME} {APP_VERSION}", self.menu)
        header_action.setEnabled(False)
        self.menu.addAction(header_action)
        self.menu.addSeparator()

        # 2. Toggle Enabled
        self.toggle_action = QAction("Enable Hover Previews", self.menu)
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(self.config.get("enabled", True))
        self.toggle_action.toggled.connect(self._on_toggle_enabled)
        self.menu.addAction(self.toggle_action)

        # 3. Quick Dwell Presets
        delay_menu = self.menu.addMenu("Hover Speed")
        delay_menu.setStyleSheet(self.menu.styleSheet())
        
        self.delay_actions = {}
        presets = [("Ultra-Fast (80 ms)", 80), ("Fast (150 ms)", 150), ("Relaxed (280 ms)", 280)]
        for label, ms in presets:
            act = QAction(label, delay_menu)
            act.setCheckable(True)
            act.setChecked(self.config.get("hover_delay_ms", 150) == ms)
            act.triggered.connect(lambda checked, val=ms: self._set_delay(val))
            delay_menu.addAction(act)
            self.delay_actions[ms] = act

        self.menu.addSeparator()

        # 4. Settings Dialog
        settings_action = QAction("Settings & Formats...", self.menu)
        settings_action.triggered.connect(self.show_settings)
        self.menu.addAction(settings_action)

        # 5. About
        about_action = QAction(f"About {APP_NAME}", self.menu)
        about_action.triggered.connect(self._show_about)
        self.menu.addAction(about_action)

        self.menu.addSeparator()

        # 6. Exit
        exit_action = QAction("Exit RawView", self.menu)
        exit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(exit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_tray_activated)

    def show(self):
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_settings()

    def _on_toggle_enabled(self, checked: bool):
        self.config["enabled"] = checked
        save_config(self.config)
        self.config_updated.emit(self.config)

    def _set_delay(self, ms: int):
        self.config["hover_delay_ms"] = ms
        for val, act in self.delay_actions.items():
            act.setChecked(val == ms)
        save_config(self.config)
        self.config_updated.emit(self.config)

    def show_settings(self):
        if not self.settings_dialog or not self.settings_dialog.isVisible():
            self.settings_dialog = SettingsDialog(self.config)
            self.settings_dialog.config_changed.connect(self._on_settings_saved)
            self.settings_dialog.exec()

    def _on_settings_saved(self, new_config: dict):
        self.config = new_config
        self.toggle_action.setChecked(self.config.get("enabled", True))
        for val, act in self.delay_actions.items():
            act.setChecked(val == self.config.get("hover_delay_ms", 150))
        self.config_updated.emit(self.config)

    def _show_about(self):
        from src.core.config import APP_PUBLISHER
        QMessageBox.about(
            None,
            f"About {APP_NAME}",
            f"<b>{APP_NAME} {APP_VERSION}</b><br>"
            f"Published by <b>{APP_PUBLISHER}</b><br><br>"
            f"Zero-Lag Hover Previewer for PSD, EPS, AI, TIFF, and SVG files.<br>"
            f"Hardware-accelerated rendering with L1/L2 multi-tier caching.<br><br>"
            f"Installed to <code>C:\\Program Files\\RawView</code>"
        )
