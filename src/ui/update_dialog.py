import os
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextBrowser, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor

from src.core.updater import UpdateDownloadWorker

class UpdatePromptDialog(QDialog):
    """Modern dark-themed glassmorphic modal prompting the user to install a new version."""

    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_worker = None
        self.downloaded_installer_path = ""

        self.setWindowTitle("RawView Update Available")
        self.setFixedSize(520, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel {
                color: #F8FAFC;
            }
            QTextBrowser {
                background-color: #1E293B;
                color: #CBD5E1;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QProgressBar {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 6px;
                text-align: center;
                color: #FFFFFF;
                font-weight: bold;
                height: 18px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #38BDF8);
                border-radius: 5px;
            }
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton#updateBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #0EA5E9);
                color: #FFFFFF;
                border: 1px solid #38BDF8;
                font-weight: 700;
            }
            QPushButton#updateBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369A1, stop:1 #0284C7);
            }
            QPushButton#updateBtn:disabled {
                background-color: #1E293B;
                color: #64748B;
                border: 1px solid #334155;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        # Header Box
        header_layout = QHBoxLayout()
        header_icon = QLabel("🚀", self)
        header_icon.setFont(QFont("Segoe UI Emoji", 26))
        header_layout.addWidget(header_icon)

        title_vbox = QVBoxLayout()
        title_lbl = QLabel("A New Update is Available!", self)
        title_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #38BDF8;")
        title_vbox.addWidget(title_lbl)

        latest_ver = self.update_info.get("latest_version", "New Version")
        cur_ver = self.update_info.get("current_version", "")
        sub_lbl = QLabel(f"RawView <b>{latest_ver}</b> is ready to install (Current: {cur_ver})", self)
        sub_lbl.setFont(QFont("Segoe UI", 11))
        sub_lbl.setStyleSheet("color: #94A3B8;")
        title_vbox.addWidget(sub_lbl)

        header_layout.addLayout(title_vbox, stretch=1)
        layout.addLayout(header_layout)

        # Version Pill Box
        pill_frame = QFrame(self)
        pill_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; border: 1px solid #334155;")
        pill_layout = QHBoxLayout(pill_frame)
        pill_layout.setContentsMargins(14, 8, 14, 8)

        rel_name = self.update_info.get("release_name", latest_ver)
        rel_label = QLabel(f"📦 Release: <b>{rel_name}</b>", pill_frame)
        rel_label.setStyleSheet("color: #E2E8F0; font-size: 12px;")
        pill_layout.addWidget(rel_label)
        pill_layout.addStretch()

        size_bytes = self.update_info.get("asset_size", 0)
        size_str = f"{size_bytes / (1024*1024):.1f} MB" if size_bytes > 0 else "Installer Package"
        size_label = QLabel(f"💾 Size: {size_str}", pill_frame)
        size_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        pill_layout.addWidget(size_label)

        layout.addWidget(pill_frame)

        # Changelog / Release Notes
        notes_hdr = QLabel("What's New in this Version:", self)
        notes_hdr.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        notes_hdr.setStyleSheet("color: #CBD5E1;")
        layout.addWidget(notes_hdr)

        self.notes_browser = QTextBrowser(self)
        raw_notes = self.update_info.get("release_notes", "").strip()
        if not raw_notes:
            raw_notes = "This release includes critical performance improvements, bug fixes, and stability enhancements."
        self.notes_browser.setPlainText(raw_notes)
        layout.addWidget(self.notes_browser, stretch=1)

        # Progress Section (Hidden until Update is clicked)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("", self)
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: #38BDF8;")
        self.status_label.hide()
        layout.addWidget(self.status_label)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.remind_btn = QPushButton("Remind Me Later", self)
        self.remind_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.remind_btn)

        btn_layout.addStretch()

        self.update_btn = QPushButton("Update Now", self)
        self.update_btn.setObjectName("updateBtn")
        self.update_btn.setMinimumWidth(130)
        self.update_btn.clicked.connect(self._start_download)
        btn_layout.addWidget(self.update_btn)

        layout.addLayout(btn_layout)

    def _start_download(self):
        download_url = self.update_info.get("download_url")
        if not download_url:
            self.status_label.setText("⚠️ Error: No installer asset found in this release.")
            self.status_label.setStyleSheet("color: #FB7185;")
            self.status_label.show()
            return

        self.update_btn.setEnabled(False)
        self.update_btn.setText("Downloading...")
        self.remind_btn.setEnabled(False)

        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("Starting download from GitHub...")
        self.status_label.setStyleSheet("color: #38BDF8;")
        self.status_label.show()

        asset_name = self.update_info.get("asset_name", "RawView_Setup.exe")
        self.download_worker = UpdateDownloadWorker(download_url, asset_name, parent=self)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.error.connect(self._on_download_error)
        self.download_worker.start()

    def _on_download_progress(self, downloaded: int, total: int, pct: float):
        self.progress_bar.setValue(int(pct))
        dl_mb = downloaded / (1024 * 1024)
        tot_mb = total / (1024 * 1024) if total > 0 else 0
        if tot_mb > 0:
            self.status_label.setText(f"Downloading installer: {dl_mb:.1f} MB / {tot_mb:.1f} MB ({pct:.1f}%)")
        else:
            self.status_label.setText(f"Downloading installer: {dl_mb:.1f} MB...")

    def _on_download_finished(self, file_path: str):
        self.downloaded_installer_path = file_path
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ Download complete! Launching updater...")
        self.status_label.setStyleSheet("color: #34D399; font-weight: bold;")

        # Launch the installer executable
        try:
            # Runs the Inno Setup installer. Inno Setup will cleanly detect the existing installation,
            # terminate the old RawView.exe, overwrite all binaries in-place, and restart RawView.
            subprocess.Popen([file_path], shell=False)
            
            # Close dialog and terminate current app so installer can overwrite cleanly
            QApplication.quit()
        except Exception as e:
            self.status_label.setText(f"Failed to launch installer: {e}")
            self.status_label.setStyleSheet("color: #FB7185;")
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Retry")

    def _on_download_error(self, error_msg: str):
        self.status_label.setText(f"❌ Download failed: {error_msg}")
        self.status_label.setStyleSheet("color: #FB7185;")
        self.update_btn.setEnabled(True)
        self.update_btn.setText("Retry")
        self.remind_btn.setEnabled(True)

    def closeEvent(self, event):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait(1000)
        super().closeEvent(event)
