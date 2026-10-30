#!/usr/bin/env python3
"""
Lightman Sound Application (PySide6)
===================================
Displays the pairing code SL-SOUND-XXXX and provides audio capture UI.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
)

from shared.config import get_logger
from shared.i18n import _, set_language, get_available_languages
from shared.pairing import BLEAdvertiser, generate_pairing_code

logger = get_logger("sound")


class SoundWindow(QMainWindow):
    """
    Main window for the Sound application.
    Displays the pairing code and provides audio controls.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(_("Lightman Sound"))
        self.resize(480, 320)

        # Generate pairing code and start advertising
        self.pairing_code = generate_pairing_code("sound")
        self.advertiser = BLEAdvertiser("sound", self.pairing_code)
        self.advertiser.start()

        # Center window
        self._center()

        # Build UI
        self._build_ui()

    def _center(self) -> None:
        """Center the window on screen."""
        frame = self.frameGeometry()
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

    def _build_ui(self) -> None:
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        central.setLayout(layout)

        # Title
        title = QLabel(_("Lightman Sound"))
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Pairing code (large text)
        code_label_title = QLabel("Pairing Code")
        code_font = QFont()
        code_font.setPointSize(14)
        code_label_title.setFont(code_font)
        layout.addWidget(code_label_title)

        self.code_display = QLabel(self.pairing_code)
        big_font = QFont()
        big_font.setPointSize(48)
        big_font.setBold(True)
        big_font.setFamily("Monaco, Consolas, monospace")
        self.code_display.setFont(big_font)
        self.code_display.setAlignment(Qt.AlignCenter)
        # Make the code stand out
        palette = self.code_display.palette()
        palette.setColor(QPalette.WindowText, QColor(0, 200, 0))
        self.code_display.setPalette(palette)
        layout.addWidget(self.code_display)

        # Device name
        device_label = QLabel(f"Advertising as: Lightman-{self.pairing_code}")
        device_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(device_label)

        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Buttons
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton(_("Start Audio"))
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        self.start_btn.clicked.connect(self._start_audio)
        btn_layout.addWidget(self.start_btn)

        self.permission_btn = QPushButton(_("Grant Permission"))
        self.permission_btn.setMinimumHeight(50)
        self.permission_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        self.permission_btn.clicked.connect(self._request_permission)
        btn_layout.addWidget(self.permission_btn)

        layout.addLayout(btn_layout)

        # Regenerate code button
        regen_btn = QPushButton("Regenerate Code")
        regen_btn.setStyleSheet("font-size: 12px; padding: 8px;")
        regen_btn.clicked.connect(self._regenerate_code)
        layout.addWidget(regen_btn)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready — advertising pairing code")

    def _start_audio(self) -> None:
        """Handle Start Audio button."""
        logger.info("Start Audio clicked — stub mode")
        self.status_bar.showMessage("Audio capture started (stub)")
        QMessageBox.information(self, _("Status"), "Audio capture started (stub mode)")

    def _request_permission(self) -> None:
        """Handle Grant Permission button."""
        logger.info("Grant Permission clicked")
        self.status_bar.showMessage("Permission requested")
        QMessageBox.information(self, _("Status"), "Microphone permission requested (stub)")

    def _regenerate_code(self) -> None:
        """Regenerate the pairing code and restart advertising."""
        self.advertiser.stop()
        self.pairing_code = generate_pairing_code("sound")
        self.advertiser = BLEAdvertiser("sound", self.pairing_code)
        self.advertiser.start()
        self.code_display.setText(self.pairing_code)
        self.status_bar.showMessage(f"New code: {self.pairing_code}")

    def closeEvent(self, event) -> None:
        """Clean up on close."""
        self.advertiser.stop()
        event.accept()


def main() -> None:
    """Entry point for the Sound application."""
    # Set default language from environment or default to English
    lang = "en"
    set_language(lang)

    app = QApplication(sys.argv)
    window = SoundWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
