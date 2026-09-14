import os
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect,
    QApplication, QFrame, QStackedWidget, QProgressBar, QPushButton, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QPoint, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal, QUrl
)
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QBrush, QPen, QImage, QPainterPath,
    QKeySequence, QShortcut, QLinearGradient
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.core.decoders import PreviewResult
from src.utils.win32_helper import calculate_popup_position

FORMAT_COLORS = {
    "PSD": ("#00C8FF", "#002B4D"),
    "PSB": ("#00C8FF", "#002B4D"),
    "AI":  ("#FF9A00", "#4A2400"),
    "EPS": ("#A855F7", "#3B0764"),
    "PDF": ("#EF4444", "#450A0A"),
    "TIFF":("#10B981", "#064E3B"),
    "TIF": ("#10B981", "#064E3B"),
    "SVG": ("#F43F5E", "#4C0519"),
    "SVGZ":("#F43F5E", "#4C0519"),
    # Microsoft Word & Documents
    "DOCX": ("#38BDF8", "#0C4A6E"),
    "DOC":  ("#38BDF8", "#0C4A6E"),
    "DOCM": ("#38BDF8", "#0C4A6E"),
    "DOTX": ("#38BDF8", "#0C4A6E"),
    "DOT":  ("#38BDF8", "#0C4A6E"),
    "RTF":  ("#60A5FA", "#1E3A8A"),
    # Microsoft Excel & CSV
    "XLSX": ("#34D399", "#064E3B"),
    "XLS":  ("#34D399", "#064E3B"),
    "XLSM": ("#34D399", "#064E3B"),
    "XLSB": ("#34D399", "#064E3B"),
    "XLTX": ("#34D399", "#064E3B"),
    "CSV":  ("#10B981", "#064E3B"),
    # Microsoft PowerPoint
    "PPTX": ("#FB923C", "#7C2D12"),
    "PPT":  ("#FB923C", "#7C2D12"),
    "PPTM": ("#FB923C", "#7C2D12"),
    "PPSX": ("#FB923C", "#7C2D12"),
    "POTX": ("#FB923C", "#7C2D12"),
    # Adobe Video & Motion Graphics Projects
    "AEP":  ("#A5B4FC", "#312E81"),
    "AET":  ("#A5B4FC", "#312E81"),
    "AEPX": ("#A5B4FC", "#312E81"),
    "PRPROJ": ("#F472B6", "#831843"),
    "PRSET":  ("#F472B6", "#831843"),
    # Video Formats
    "MP4": ("#38BDF8", "#0369A1"),
    "MKV": ("#10B981", "#064E3B"),
    "MOV": ("#A855F7", "#3B0764"),
    "AVI": ("#F59E0B", "#451A03"),
    "WMV": ("#06B6D4", "#164E63"),
    "WEBM":("#EC4899", "#831843"),
    "FLV": ("#F43F5E", "#881337"),
    "M4V": ("#38BDF8", "#0369A1"),
    "TS":  ("#6366F1", "#312E81"),
    "3GP": ("#84CC16", "#365314"),
    "MPG": ("#EAB308", "#713F12"),
    "MPEG":("#EAB308", "#713F12"),
    # Camera RAW
    "DNG": ("#F59E0B", "#451A03"),
    "CR2": ("#F59E0B", "#451A03"),
    "CR3": ("#F59E0B", "#451A03"),
    "CRW": ("#F59E0B", "#451A03"),
    "NEF": ("#F59E0B", "#451A03"),
    "NRW": ("#F59E0B", "#451A03"),
    "ARW": ("#F59E0B", "#451A03"),
    "SRF": ("#F59E0B", "#451A03"),
    "SR2": ("#F59E0B", "#451A03"),
    "RAF": ("#F59E0B", "#451A03"),
    "ORF": ("#F59E0B", "#451A03"),
    "ORI": ("#F59E0B", "#451A03"),
    "RW2": ("#F59E0B", "#451A03"),
    "PEF": ("#F59E0B", "#451A03"),
    "PTX": ("#F59E0B", "#451A03"),
    "3FR": ("#F59E0B", "#451A03"),
    "FFF": ("#F59E0B", "#451A03"),
    "IIQ": ("#F59E0B", "#451A03"),
    "RAW": ("#F59E0B", "#451A03"),
    "X3F": ("#F59E0B", "#451A03"),
}

class ImageCanvas(QLabel):
    """
    High-definition viewport widget displaying images with alpha checkerboard,
    zero-pixelation scaling from full-resolution master buffer, and mouse drag-to-pan.
    """
    zoom_changed = pyqtSignal(int) # Emits zoom percentage (e.g. 100, 150, 200)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(280, 180)
        self.setMouseTracking(True)

        self._source_qimage = QImage()
        self._cached_pixmap = QPixmap()
        self.zoom_factor = 1.0
        self.max_display_w = 640
        self.max_display_h = 480

        self._pan_offset = QPoint(0, 0)
        self._is_panning = False
        self._drag_start_pos = QPoint()
        self._drag_start_offset = QPoint()

    def set_image(self, qimage: QImage, max_w: int = 640, max_h: int = 480):
        self._source_qimage = qimage.copy() if not qimage.isNull() else QImage()
        self.max_display_w = max_w
        self.max_display_h = max_h
        self.reset_view()

    def reset_view(self):
        self.zoom_factor = 1.0
        self._pan_offset = QPoint(0, 0)
        self._is_panning = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._update_scaled_pixmap()
        self.zoom_changed.emit(100)
        self.update()

    def _get_base_fitted_size(self) -> QSize:
        if self._source_qimage.isNull():
            return QSize(self.max_display_w, self.max_display_h)
        orig_w = self._source_qimage.width()
        orig_h = self._source_qimage.height()
        if orig_w <= 0 or orig_h <= 0:
            return QSize(self.max_display_w, self.max_display_h)

        # Scale image to fill available display area while preserving aspect ratio.
        # Both small and large images are fitted (upscaled or downscaled) to maximize
        # the preview area usage, eliminating excessive empty space around small images.
        aspect = orig_w / orig_h
        if (self.max_display_w / max(self.max_display_h, 1)) > aspect:
            h = self.max_display_h
            w = int(h * aspect)
        else:
            w = self.max_display_w
            h = int(w / aspect)

        # Quality cap: don't upscale beyond 2x to avoid blurriness on tiny thumbnails.
        # A 256px XMP thumbnail stretched to 640px (2.5x) looks terrible; cap at 512px (2x).
        max_upscale = 2.0
        if w > orig_w * max_upscale or h > orig_h * max_upscale:
            w = min(w, int(orig_w * max_upscale))
            h = min(h, int(orig_h * max_upscale))

        return QSize(max(w, 100), max(h, 80))

    def _update_scaled_pixmap(self):
        if self._source_qimage.isNull():
            self._cached_pixmap = QPixmap()
            return

        base_sz = self._get_base_fitted_size()
        target_w = max(int(base_sz.width() * self.zoom_factor), 10)
        target_h = max(int(base_sz.height() * self.zoom_factor), 10)

        src_w = self._source_qimage.width()
        src_h = self._source_qimage.height()

        # Choose transformation mode based on whether we are upscaling or downscaling:
        #   Upscaling  (target > source): FastTransformation (nearest-neighbor) — pixel-perfect, no blur
        #   Downscaling (target ≤ source): SmoothTransformation (bilinear)     — anti-aliased, smooth
        #
        # This is smarter than a fixed zoom-factor threshold because large images (e.g. 4167px)
        # are still being DOWNSCALED even at 800% zoom (target=3840 < src=4167), so they benefit
        # from SmoothTransformation. Small images begin upscaling at much lower zoom levels.
        if target_w > src_w or target_h > src_h:
            transform_mode = Qt.TransformationMode.FastTransformation
        else:
            transform_mode = Qt.TransformationMode.SmoothTransformation

        # Scale directly from full-resolution master buffer
        scaled_qim = self._source_qimage.scaled(
            target_w, target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            transform_mode
        )
        self._cached_pixmap = QPixmap.fromImage(scaled_qim)


    def zoom(self, factor: float, center_point: QPoint = None):
        old_zoom = self.zoom_factor
        self.zoom_factor = max(0.5, min(self.zoom_factor * factor, 8.0))
        
        if abs(self.zoom_factor - old_zoom) > 0.001:
            self._update_scaled_pixmap()
            self._clamp_pan()
            self.zoom_changed.emit(int(round(self.zoom_factor * 100)))
            
            if self.zoom_factor > 1.0:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

    def _clamp_pan(self):
        if self._cached_pixmap.isNull():
            self._pan_offset = QPoint(0, 0)
            return

        vw = self.width()
        vh = self.height()
        pw = self._cached_pixmap.width()
        ph = self._cached_pixmap.height()

        if pw <= vw:
            max_x = 0
            min_x = 0
        else:
            max_x = (pw - vw) // 2
            min_x = -max_x

        if ph <= vh:
            max_y = 0
            min_y = 0
        else:
            max_y = (ph - vh) // 2
            min_y = -max_y

        clamped_x = max(min_x, min(self._pan_offset.x(), max_x))
        clamped_y = max(min_y, min(self._pan_offset.y(), max_y))
        self._pan_offset = QPoint(clamped_x, clamped_y)

    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            if self.zoom_factor > 1.0:
                self._is_panning = True
                self._drag_start_pos = event.pos()
                self._drag_start_offset = QPoint(self._pan_offset)
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.pos() - self._drag_start_pos
            self._pan_offset = self._drag_start_offset + delta
            self._clamp_pan()
            self.update()
            event.accept()
            return
        elif self.zoom_factor > 1.0:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_panning:
            self._is_panning = False
            if self.zoom_factor > 1.0:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Double click resets zoom and pan
        self.reset_view()
        event.accept()

    def sizeHint(self) -> QSize:
        if self._source_qimage.isNull():
            return QSize(self.max_display_w, self.max_display_h)
        return self._get_base_fitted_size()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw subtle checkerboard pattern for alpha transparency
        rect = self.rect()
        tile_size = 12
        light_color = QColor(25, 29, 40)
        dark_color = QColor(18, 21, 30)

        for x in range(0, rect.width(), tile_size):
            for y in range(0, rect.height(), tile_size):
                color = light_color if ((x // tile_size) + (y // tile_size)) % 2 == 0 else dark_color
                painter.fillRect(x, y, tile_size, tile_size, color)

        # Draw high-definition scaled pixmap with pan offset
        if not self._cached_pixmap.isNull():
            draw_x = (rect.width() - self._cached_pixmap.width()) // 2 + self._pan_offset.x()
            draw_y = (rect.height() - self._cached_pixmap.height()) // 2 + self._pan_offset.y()
            painter.drawPixmap(draw_x, draw_y, self._cached_pixmap)

        painter.end()

class VideoPlayerWidget(QWidget):
    """
    Hardware-accelerated live video player with muted looping,
    playback progress bar, and instant start/stop for hover previews.
    """
    playback_time_changed = pyqtSignal(int, int) # (pos_ms, dur_ms)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 180)
        self.max_display_w = 640
        self.max_display_h = 480
        self.aspect_ratio = 16.0 / 9.0
        self._last_pct = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video Output Viewport (hardware-accelerated opaque paint)
        self.video_widget = QVideoWidget(self)
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.video_widget.setStyleSheet("background-color: #000000;")
        layout.addWidget(self.video_widget, stretch=1)

        # Sleek Micro Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #38BDF8;
                border-radius: 1px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Media Player & Audio Output
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.audio_output.setMuted(True)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

    def set_video_dimensions(self, width: int, height: int, max_w: int = 640, max_h: int = 480):
        self.max_display_w = max_w
        self.max_display_h = max_h
        if width > 0 and height > 0:
            self.aspect_ratio = width / height
        else:
            self.aspect_ratio = 16.0 / 9.0

    def sizeHint(self) -> QSize:
        if (self.max_display_w / max(self.max_display_h, 1)) > self.aspect_ratio:
            h = min(self.max_display_h, 480)
            w = int(h * self.aspect_ratio)
        else:
            w = min(self.max_display_w, 640)
            h = int(w / self.aspect_ratio)
        return QSize(max(w, 240), max(h, 140))

    def play_video(self, file_path: str):
        self.player.stop()
        self.progress_bar.setValue(0)
        url = QUrl.fromLocalFile(file_path) if not file_path.startswith("http") and not file_path.startswith("ftp") else QUrl(file_path)
        self.player.setSource(url)
        self.player.play()

    def stop_video(self):
        self.player.stop()
        self.player.setSource(QUrl())
        self.progress_bar.setValue(0)

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_position_changed(self, pos_ms: int):
        dur = self.player.duration()
        if dur > 0:
            pct = int((pos_ms / dur) * 100)
            if pct != self._last_pct:
                self._last_pct = pct
                self.progress_bar.setValue(pct)
        self.playback_time_changed.emit(pos_ms, dur)

    def _on_duration_changed(self, dur_ms: int):
        pos = self.player.position()
        self.playback_time_changed.emit(pos, dur_ms)

from PyQt6.QtGui import QDesktopServices
from src.core.licensing import get_license_status, get_machine_id
from src.core.config import PAYMENT_INFO

class TrialExpiredCard(QWidget):
    """Sleek glassmorphic card displayed when 7-day free trial expires."""
    open_settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # Title & Price Header
        title = QLabel("🔒 7-Day Free Trial Ended", self)
        title.setStyleSheet("color: #FB7185; font-size: 16px; font-weight: 700;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Unlock unlimited Lifetime Pro access for only <b>50 TK</b>!", self)
        sub.setStyleSheet("color: #38BDF8; font-size: 13px; font-weight: 600;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        # 1. Machine Code Box
        mid_card = QFrame(self)
        mid_card.setStyleSheet("background-color: rgba(30, 41, 59, 0.85); border: 1px solid #334155; border-radius: 8px; padding: 4px;")
        mid_layout = QHBoxLayout(mid_card)
        mid_layout.setContentsMargins(10, 4, 10, 4)

        mid_label = QLabel("1. Your Machine Code:", mid_card)
        mid_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        
        self.mid_text = QLabel(get_machine_id(), mid_card)
        self.mid_text.setStyleSheet("color: #38BDF8; font-weight: 700; font-family: monospace; font-size: 12px;")

        copy_btn = QPushButton("📋 Copy Code", mid_card)
        copy_btn.setStyleSheet("background-color: #0284C7; color: white; border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: 600;")
        copy_btn.clicked.connect(self._copy_mid)

        mid_layout.addWidget(mid_label)
        mid_layout.addWidget(self.mid_text, stretch=1)
        mid_layout.addWidget(copy_btn)
        layout.addWidget(mid_card)

        # 2. bKash Payment Box
        bkash_card = QFrame(self)
        bkash_card.setStyleSheet("background-color: rgba(30, 41, 59, 0.85); border: 1px solid #E11D48; border-radius: 8px; padding: 4px;")
        bkash_layout = QHBoxLayout(bkash_card)
        bkash_layout.setContentsMargins(10, 4, 10, 4)

        bkash_label = QLabel("2. bKash Personal (50 TK):", bkash_card)
        bkash_label.setStyleSheet("color: #FB7185; font-size: 11px; font-weight: 700;")

        self.bkash_val = QLabel(PAYMENT_INFO.get("bkash_number", "01756678087"), bkash_card)
        self.bkash_val.setStyleSheet("color: #FFFFFF; font-weight: 700; font-family: monospace; font-size: 12px;")

        copy_bkash_btn = QPushButton("📋 Copy Number", bkash_card)
        copy_bkash_btn.setStyleSheet("background-color: #E11D48; color: white; border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: 600;")
        copy_bkash_btn.clicked.connect(self._copy_bkash)

        bkash_layout.addWidget(bkash_label)
        bkash_layout.addWidget(self.bkash_val, stretch=1)
        bkash_layout.addWidget(copy_bkash_btn)
        layout.addWidget(bkash_card)

        # 3. WhatsApp Support Link
        wa_card = QFrame(self)
        wa_card.setStyleSheet("background-color: rgba(30, 41, 59, 0.85); border: 1px solid #10B981; border-radius: 8px; padding: 4px;")
        wa_layout = QHBoxLayout(wa_card)
        wa_layout.setContentsMargins(10, 4, 10, 4)

        wa_label = QLabel("3. WhatsApp Support:", wa_card)
        wa_label.setStyleSheet("color: #34D399; font-size: 11px; font-weight: 700;")

        wa_val = QLabel(PAYMENT_INFO.get("whatsapp_number", "+1 (202) 780-6050"), wa_card)
        wa_val.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 12px;")

        open_wa_btn = QPushButton("💬 Open WhatsApp", wa_card)
        open_wa_btn.setStyleSheet("background-color: #059669; color: white; border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: 700;")
        open_wa_btn.clicked.connect(self._open_whatsapp)

        wa_layout.addWidget(wa_label)
        wa_layout.addWidget(wa_val, stretch=1)
        wa_layout.addWidget(open_wa_btn)
        layout.addWidget(wa_card)

        # Action Button to open settings
        btn_layout = QHBoxLayout()
        activate_btn = QPushButton("⚡ Enter License Key & Activate Pro", self)
        activate_btn.setStyleSheet("""
            background-color: #0284C7;
            color: #FFFFFF;
            border: 1px solid #38BDF8;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 700;
        """)
        activate_btn.clicked.connect(self.open_settings_requested.emit)
        btn_layout.addWidget(activate_btn)

        layout.addLayout(btn_layout)

    def _copy_mid(self):
        mid = self.mid_text.text()
        QApplication.clipboard().setText(mid)

    def _copy_bkash(self):
        num = self.bkash_val.text()
        QApplication.clipboard().setText(num)

    def _open_whatsapp(self):
        mid = self.mid_text.text()
        msg = f"Hello! I sent 50 TK for RawView Lifetime Pro.\nMy Machine Code: {mid}"
        url_str = f"https://wa.me/12027806050?text={msg.replace(' ', '%20').replace('\n', '%0A')}"
        QDesktopServices.openUrl(QUrl(url_str))

class PageThumbnailCard(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, page_idx: int, thumb_img: QImage = None, parent=None):
        super().__init__(parent)
        self.page_idx = page_idx
        self.is_active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(82)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        self.thumb_label = QLabel(self)
        self.thumb_label.setFixedSize(74, 96)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #121622; border-radius: 4px;")

        if thumb_img and not thumb_img.isNull():
            pix = QPixmap.fromImage(thumb_img).scaled(
                74, 96,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumb_label.setPixmap(pix)

        layout.addWidget(self.thumb_label)

        self.name_label = QLabel(f"Page {page_idx + 1}", self)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 600;")
        layout.addWidget(self.name_label)

        self._update_style()

    def set_thumbnail(self, thumb_img: QImage):
        if thumb_img and not thumb_img.isNull():
            pix = QPixmap.fromImage(thumb_img).scaled(
                74, 96,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumb_label.setPixmap(pix)

    def set_active(self, active: bool):
        self.is_active = active
        self._update_style()

    def _update_style(self):
        if self.is_active:
            self.setStyleSheet("""
                PageThumbnailCard {
                    background-color: rgba(56, 189, 248, 0.15);
                    border: 1.5px solid #38BDF8;
                    border-radius: 6px;
                }
            """)
            self.name_label.setStyleSheet("color: #38BDF8; font-size: 10px; font-weight: 700;")
        else:
            self.setStyleSheet("""
                PageThumbnailCard {
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 6px;
                }
                PageThumbnailCard:hover {
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(56, 189, 248, 0.5);
                }
            """)
            self.name_label.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 600;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.page_idx)
            event.accept()
        else:
            super().mousePressEvent(event)


class PageThumbnailSidebar(QFrame):
    page_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.current_idx = 0
        self.setFixedWidth(98)
        self.setStyleSheet("""
            PageThumbnailSidebar {
                background-color: rgba(12, 16, 26, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)

        # Header with badge
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 0, 2, 0)
        self.header_label = QLabel("PAGES", self)
        self.header_label.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        header_layout.addWidget(self.header_label)

        self.count_badge = QLabel("0", self)
        self.count_badge.setStyleSheet("color: #38BDF8; font-size: 10px; font-weight: 700; background: rgba(56, 189, 248, 0.15); padding: 1px 4px; border-radius: 3px;")
        header_layout.addWidget(self.count_badge, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header_layout)

        # Scroll area for page thumbnails
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 2, 0, 2)
        self.cards_layout.setSpacing(6)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, stretch=1)

        # Hint at bottom
        self.hint_label = QLabel("Space: Pin", self)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("color: #475569; font-size: 9px; font-weight: 600; padding: 2px 0;")
        layout.addWidget(self.hint_label)

    def set_pages(self, count: int, thumbnails: list, active_idx: int = 0):
        # Clear existing cards
        for c in self.cards:
            c.setParent(None)
            c.deleteLater()
        self.cards.clear()

        self.current_idx = active_idx
        self.count_badge.setText(str(count))

        for idx in range(count):
            thumb = thumbnails[idx] if thumbnails and idx < len(thumbnails) else None
            card = PageThumbnailCard(idx, thumb, self.scroll_content)
            card.clicked.connect(self._on_card_clicked)
            if idx == active_idx:
                card.set_active(True)
            self.cards.append(card)
            self.cards_layout.addWidget(card)

    def set_active_page(self, idx: int):
        if 0 <= idx < len(self.cards):
            self.current_idx = idx
            for i, c in enumerate(self.cards):
                c.set_active(i == idx)
            card = self.cards[idx]
            self.scroll_area.ensureWidgetVisible(card)

    def update_pin_status(self, is_pinned: bool):
        if is_pinned:
            self.hint_label.setText("PINNED")
            self.hint_label.setStyleSheet("color: #38BDF8; font-size: 9px; font-weight: 700; padding: 2px 0;")
        else:
            self.hint_label.setText("Space: Pin")
            self.hint_label.setStyleSheet("color: #475569; font-size: 9px; font-weight: 600; padding: 2px 0;")

    def _on_card_clicked(self, idx: int):
        self.set_active_page(idx)
        self.page_selected.emit(idx)


class FloatingPreviewHUD(QWidget):
    """
    Hardware-accelerated, glassmorphic floating preview window for RawView v3.1.5.
    Seamlessly renders full-resolution images, documents, live video playback,
    and handles 7-day unlimited trial + Lifetime Pro activation states.
    """
    pin_state_changed = pyqtSignal(bool)
    visibility_changed = pyqtSignal(bool)
    open_settings_requested = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.max_view_size = config.get("preview_max_size", 640)
        self.is_pinned = False
        self.current_file_path = ""
        self.current_result = None
        self._last_video_p_sec = -1
        self._last_video_d_sec = -1

        self._init_window_flags()
        self._init_ui()
        self._init_animations()
        self._init_shortcuts()

    def _init_window_flags(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.ToolTip |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    def _init_ui(self):
        # Main Outer Container
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)

        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background-color: rgba(15, 18, 28, 0.96);
                border: 1px solid rgba(80, 120, 200, 0.35);
                border-radius: 14px;
            }
        """)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(14, 12, 14, 12)
        container_layout.setSpacing(10)

        # 1. Header Bar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Format Badge
        self.format_badge = QLabel("PSD", self)
        self.format_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.format_badge.setStyleSheet("""
            background-color: #002B4D;
            color: #00C8FF;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 5px;
            border: 1px solid rgba(0, 200, 255, 0.3);
        """)
        header_layout.addWidget(self.format_badge)

        # File Name Label
        self.title_label = QLabel("file_preview.psd", self)
        self.title_label.setStyleSheet("""
            color: #F0F4F8;
            font-size: 13px;
            font-weight: 600;
        """)
        header_layout.addWidget(self.title_label, stretch=1)

        # Pin Status Indicator
        self.pin_label = QLabel("Space to Pin", self)
        self.pin_label.setStyleSheet("""
            color: #64748B;
            font-size: 10px;
            font-weight: 500;
            padding: 2px 6px;
            border-radius: 4px;
            background-color: rgba(255, 255, 255, 0.05);
        """)
        header_layout.addWidget(self.pin_label)

        container_layout.addLayout(header_layout)

        # 2. Main Body: Horizontal layout with Page Thumbnail Sidebar on Left + Viewport Stack
        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(8)

        self.page_sidebar = PageThumbnailSidebar(self)
        self.page_sidebar.page_selected.connect(self._on_page_selected)
        self.page_sidebar.hide()
        self.body_layout.addWidget(self.page_sidebar)

        self.viewport_stack = QStackedWidget(self)
        self.viewport_stack.setStyleSheet("background-color: transparent;")

        self.canvas = ImageCanvas(self)
        self.canvas.zoom_changed.connect(self._on_zoom_changed)
        self.canvas.setStyleSheet("""
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            background-color: #12151E;
        """)
        self.viewport_stack.addWidget(self.canvas)

        self.video_player = VideoPlayerWidget(self)
        self.video_player.playback_time_changed.connect(self._on_video_time_changed)
        self.viewport_stack.addWidget(self.video_player)

        self.trial_card = TrialExpiredCard(self)
        self.trial_card.open_settings_requested.connect(self._on_open_settings)
        self.viewport_stack.addWidget(self.trial_card)

        self.body_layout.addWidget(self.viewport_stack, stretch=1)
        container_layout.addLayout(self.body_layout, stretch=1)

        # 3. Metadata Footer Bar
        self.footer_layout = QHBoxLayout()
        self.footer_layout.setSpacing(12)

        self.dim_label = QLabel("3840 × 2160 px", self)
        self.dim_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 500;")
        self.footer_layout.addWidget(self.dim_label)

        self.mode_label = QLabel("RGB", self)
        self.mode_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 500;")
        self.footer_layout.addWidget(self.mode_label)

        # Zoom / Video / License Status Badge
        self.zoom_badge = QLabel("100%", self)
        self.zoom_badge.setStyleSheet("""
            color: #A78BFA;
            font-size: 10px;
            font-weight: 600;
            padding: 1px 5px;
            border-radius: 3px;
            background-color: rgba(167, 139, 250, 0.15);
        """)
        self.footer_layout.addWidget(self.zoom_badge)

        self.footer_layout.addStretch()

        # License status mini badge
        self.lic_badge = QLabel("✨ PRO", self)
        self.lic_badge.setStyleSheet("color: #10B981; font-size: 10px; font-weight: 700;")
        self.footer_layout.addWidget(self.lic_badge)

        self.size_label = QLabel("14.5 MB", self)
        self.size_label.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600;")
        self.footer_layout.addWidget(self.size_label)

        container_layout.addLayout(self.footer_layout)
        self.main_layout.addWidget(self.container)

    def _init_animations(self):
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(120)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _init_shortcuts(self):
        # Space: Pin / Unpin or Play / Pause
        self.pin_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.pin_shortcut.activated.connect(self.toggle_pin)

        # Esc: Dismiss
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.esc_shortcut.activated.connect(self.dismiss)

        # Ctrl+C: Copy Image
        self.copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.copy_shortcut.activated.connect(self.copy_image_to_clipboard)

        # Ctrl+O / Return / Enter: Open File
        self.open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        self.open_shortcut.activated.connect(self.open_current_file)
        self.return_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        self.return_shortcut.activated.connect(self.open_current_file)
        self.enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Enter), self)
        self.enter_shortcut.activated.connect(self.open_current_file)

        # Multi-page Document Navigation (Down / Up / PageDown / PageUp)
        self.down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.down_shortcut.activated.connect(self.select_next_page)
        self.up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.up_shortcut.activated.connect(self.select_prev_page)
        self.pagedown_shortcut = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        self.pagedown_shortcut.activated.connect(self.select_next_page)
        self.pageup_shortcut = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        self.pageup_shortcut.activated.connect(self.select_prev_page)

    def _on_open_settings(self):
        self.dismiss()
        self.open_settings_requested.emit()

    def _on_zoom_changed(self, percent: int):
        if not self.current_result or not self.current_result.is_video:
            self.zoom_badge.setText(f"{percent}%")
            if percent != 100:
                self.zoom_badge.setStyleSheet("""
                    color: #F59E0B;
                    font-size: 10px;
                    font-weight: 700;
                    padding: 1px 5px;
                    border-radius: 3px;
                    background-color: rgba(245, 158, 11, 0.2);
                """)
            else:
                self.zoom_badge.setStyleSheet("""
                    color: #A78BFA;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 1px 5px;
                    border-radius: 3px;
                    background-color: rgba(167, 139, 250, 0.15);
                """)

    def _on_video_time_changed(self, pos_ms: int, dur_ms: int):
        if self.current_result and self.current_result.is_video:
            p_sec = int(pos_ms // 1000)
            d_sec = int(dur_ms // 1000) if dur_ms > 0 else 0
            if p_sec != self._last_video_p_sec or d_sec != self._last_video_d_sec:
                self._last_video_p_sec = p_sec
                self._last_video_d_sec = d_sec
                time_str = f"{p_sec // 60}:{p_sec % 60:02d} / {d_sec // 60}:{d_sec % 60:02d}"
                self.mode_label.setText(time_str)

    def display_preview(self, file_path: str, result: PreviewResult, cursor_x: int, cursor_y: int):
        self.current_file_path = file_path
        self.current_result = result
        self._last_video_p_sec = -1
        self._last_video_d_sec = -1

        # Check License Status
        lic_info = get_license_status()
        is_unlocked = lic_info.get("is_unlocked", True)
        lic_status = lic_info.get("status")

        # Update license badge in footer
        if lic_status == "PRO_ACTIVE":
            self.lic_badge.setText("✨ PRO")
            self.lic_badge.setStyleSheet("color: #34D399; font-size: 10px; font-weight: 700;")
        elif lic_status == "TRIAL_ACTIVE":
            days = lic_info.get("days_left", 7)
            self.lic_badge.setText(f"⏳ Trial: {days}d left")
            self.lic_badge.setStyleSheet("color: #38BDF8; font-size: 10px; font-weight: 600;")
        else:
            self.lic_badge.setText("🔒 Expired")
            self.lic_badge.setStyleSheet("color: #FB7185; font-size: 10px; font-weight: 700;")

        # If trial expired -> Display Trial Expired Card
        if not is_unlocked:
            self.page_sidebar.hide()
            self.video_player.stop_video()
            self.viewport_stack.setCurrentWidget(self.trial_card)
            fname = Path(file_path).name if not file_path.startswith("ftp://") else file_path.split("/")[-1]
            self.title_label.setText(fname)
            self.format_badge.setText("PRO")
            self.format_badge.setStyleSheet("background-color: #4C0519; color: #FB7185; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 5px;")
            self.dim_label.setText("Activation Required")
            self.mode_label.setText("50 TK Lifetime")
            self.size_label.setText(result.formatted_size)
            self.zoom_badge.setText("Locked")
            self.zoom_badge.setStyleSheet("color: #FB7185; font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 3px; background-color: rgba(251, 113, 133, 0.2);")

            self.adjustSize()
            w = self.width()
            h = self.height()
            pos = calculate_popup_position(cursor_x, cursor_y, w, h)
            self.move(pos)
            self.setWindowOpacity(1.0)
            self.show()
            self.raise_()
            self.visibility_changed.emit(True)
            return

        # Setup multi-page sidebar if document has multiple pages
        page_count = getattr(result, "page_count", 1)
        if page_count > 1:
            self.page_sidebar.set_pages(page_count, result.page_thumbnails, active_idx=result.current_page_idx)
            self.page_sidebar.update_pin_status(self.is_pinned)
            self.page_sidebar.show()
            if not self.is_pinned:
                self.pin_label.setText("Space to Pin & Browse")
        else:
            self.page_sidebar.hide()
            if not self.is_pinned:
                self.pin_label.setText("Space to Pin")

        # Update Header
        fname = Path(file_path).name if not file_path.startswith("ftp://") else file_path.split("/")[-1]
        self.title_label.setText(fname)
        self.title_label.setToolTip(file_path)

        fmt = result.format_name.upper()
        self.format_badge.setText(fmt)
        fg_col, bg_col = FORMAT_COLORS.get(fmt, ("#38BDF8", "#0369A1"))
        self.format_badge.setStyleSheet(f"""
            background-color: {bg_col};
            color: {fg_col};
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 5px;
            border: 1px solid {fg_col}55;
        """)

        # Display Live Video vs Image Canvas
        if result.is_video:
            self.viewport_stack.setCurrentWidget(self.video_player)
            self.video_player.set_video_dimensions(result.width, result.height, max_w=self.max_view_size, max_h=int(self.max_view_size * 0.75))
            target_video = result.video_path if result.video_path else file_path
            self.video_player.play_video(target_video)
            self.dim_label.setText(result.dimensions_str)
            self.mode_label.setText("Playing")
            self.zoom_badge.setText("Live Video")
            self.zoom_badge.setStyleSheet("""
                color: #10B981;
                font-size: 10px;
                font-weight: 700;
                padding: 1px 5px;
                border-radius: 3px;
                background-color: rgba(16, 185, 129, 0.2);
            """)
        else:
            self.video_player.stop_video()
            self.viewport_stack.setCurrentWidget(self.canvas)
            self.canvas.set_image(result.qimage, max_w=self.max_view_size, max_h=int(self.max_view_size * 0.75))
            self.dim_label.setText(result.dimensions_str)
            if page_count > 1:
                self.mode_label.setText(f"Page {result.current_page_idx + 1} of {page_count}")
            else:
                self.mode_label.setText(result.mode)
            self.zoom_badge.setText("100%")
            self.zoom_badge.setStyleSheet("""
                color: #A78BFA;
                font-size: 10px;
                font-weight: 600;
                padding: 1px 5px;
                border-radius: 3px;
                background-color: rgba(167, 139, 250, 0.15);
            """)

        # Update Size Metadata
        self.size_label.setText(result.formatted_size)

        # Auto-adjust window size
        self.adjustSize()
        w = self.width()
        h = self.height()

        # Position cleanly near cursor
        pos = calculate_popup_position(cursor_x, cursor_y, w, h)
        self.move(pos)

        # Display window
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self.visibility_changed.emit(True)

    def _on_page_selected(self, page_idx: int):
        if not self.current_result:
            return
        if not self.is_pinned:
            self.toggle_pin()
        self.current_result.current_page_idx = page_idx
        page_img = self.current_result.get_page(page_idx)
        if page_img and not page_img.isNull():
            self.canvas.set_image(page_img, max_w=self.max_view_size, max_h=int(self.max_view_size * 0.75))
            self.page_sidebar.set_active_page(page_idx)
            total = self.current_result.page_count
            self.mode_label.setText(f"Page {page_idx + 1} of {total}")
            dim_str = f"{page_img.width()} × {page_img.height()} px"
            self.dim_label.setText(dim_str)

    def select_next_page(self):
        if self.current_result and getattr(self.current_result, "page_count", 1) > 1:
            idx = self.current_result.current_page_idx + 1
            if idx < self.current_result.page_count:
                self._on_page_selected(idx)

    def select_prev_page(self):
        if self.current_result and getattr(self.current_result, "page_count", 1) > 1:
            idx = self.current_result.current_page_idx - 1
            if idx >= 0:
                self._on_page_selected(idx)

    def toggle_pin(self):
        if not self.isVisible():
            return
        self.is_pinned = not self.is_pinned
        self.pin_state_changed.emit(self.is_pinned)
        self.page_sidebar.update_pin_status(self.is_pinned)
        
        if self.is_pinned:
            self.pin_label.setText("PINNED (Space to Unpin)")
            self.pin_label.setStyleSheet("""
                color: #38BDF8;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 6px;
                border-radius: 4px;
                background-color: rgba(56, 189, 248, 0.2);
                border: 1px solid rgba(56, 189, 248, 0.4);
            """)
            self.activateWindow()
        else:
            page_count = getattr(self.current_result, "page_count", 1) if self.current_result else 1
            if page_count > 1:
                self.pin_label.setText("Space to Pin & Browse")
            else:
                self.pin_label.setText("Space to Pin")
            self.pin_label.setStyleSheet("""
                color: #64748B;
                font-size: 10px;
                font-weight: 500;
                padding: 2px 6px;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.05);
            """)
            # Immediately dismiss preview upon unpinning
            self.dismiss()

    def dismiss(self):
        self.is_pinned = False
        self.pin_state_changed.emit(False)
        self.video_player.stop_video()
        self.canvas.reset_view()
        self.page_sidebar.hide()
        self.hide()
        self.visibility_changed.emit(False)

    def copy_image_to_clipboard(self):
        if self.current_result and not self.current_result.qimage.isNull():
            clipboard = QApplication.clipboard()
            clipboard.setImage(self.current_result.qimage)

    def open_current_file(self):
        if self.current_file_path and os.path.exists(self.current_file_path):
            os.startfile(self.current_file_path)
            self.dismiss()

    def wheelEvent(self, event):
        if self.current_result and not self.current_result.is_video:
            delta = event.angleDelta().y()
            if delta > 0:
                self.canvas.zoom(1.2)
            elif delta < 0:
                self.canvas.zoom(0.83)
            event.accept()
