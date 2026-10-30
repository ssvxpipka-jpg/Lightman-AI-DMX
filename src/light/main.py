#!/usr/bin/env python3
"""
Lightman Light Application (PySide6)
====================================
Displays the pairing code SL-LIGHT-XXXX and provides console control UI.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpacerItem, QSizePolicy, QComboBox, QLineEdit,
    QMessageBox,
)

from shared.config import get_logger
from shared.i18n import _, set_language
from shared.pairing import BLEAdvertiser, generate_pairing_code

logger = get_logger("light")

CONSOLE_TYPES = [
    ("Titan WebAPI", "titan_webapi"),
    ("GrandMA3", "grandma3"),
    ("GrandMA2", "grandma2"),
    ("ChamSys", "chamsys"),
    ("ETC Eos", "eos"),
    ("QLC+", "qlcplus"),
]


class LightWindow(QMainWindow):
    """Main window for the Light application."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(_("Lightman Light"))
        self.resize(520, 400)

        self.pairing_code = generate_pairing_code("light")
        self.advertiser = BLEAdvertiser("light", self.pairing_code)
        self.advertiser.start()

        self._center()
        self._build_ui()

    def _center(self) -> None:
        frame = self.frameGeometry()
        screen = QGuiApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        title = QLabel(_("Lightman Light"))
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        code_title = QLabel("Pairing Code")
        code_font = QFont()
        code_font.setPointSize(14)
        code_title.setFont(code_font)
        layout.addWidget(code_title)

        self.code_display = QLabel(self.pairing_code)
        big_font = QFont()
        big_font.setPointSize(48)
        big_font.setBold(True)
        big_font.setFamily("Monaco, Consolas, monospace")
        self.code_display.setFont(big_font)
        self.code_display.setAlignment(Qt.AlignCenter)
        palette = self.code_display.palette()
        palette.setColor(QPalette.WindowText, QColor(200, 100, 255))
        self.code_display.setPalette(palette)
        layout.addWidget(self.code_display)

        device_label = QLabel(f"Advertising as: Lightman-{self.pairing_code}")
        device_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(device_label)

        # Console selection
        console_label = QLabel(_("Console Type"))
        layout.addWidget(console_label)

        self.console_combo = QComboBox()
        for label, value in CONSOLE_TYPES:
            self.console_combo.addItem(label, value)
        layout.addWidget(self.console_combo)

        # Host/Port fields
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("127.0.0.1")
        host_layout.addWidget(self.host_input)
        host_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("")
        host_layout.addWidget(self.port_input)
        layout.addLayout(host_layout)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        status_label = QLabel(_("Console Status"))
        status_label_font = QFont()
        status_label_font.setBold(True)
        status_label.setFont(status_label_font)
        layout.addWidget(status_label)

        self.status_display = QLabel("Disconnected")
        self.status_display.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.status_display)

        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton(_("Connect Console"))
        self.connect_btn.setMinimumHeight(50)
        self.connect_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        self.connect_btn.clicked.connect(self._connect_console)
        btn_layout.addWidget(self.connect_btn)

        self.plugins_btn = QPushButton("Plugins")
        self.plugins_btn.setMinimumHeight(50)
        self.plugins_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        self.plugins_btn.clicked.connect(self._open_plugins)
        btn_layout.addWidget(self.plugins_btn)
        layout.addLayout(btn_layout)

        regen_btn = QPushButton("Regenerate Code")
        regen_btn.setStyleSheet("font-size: 12px; padding: 8px;")
        regen_btn.clicked.connect(self._regenerate_code)
        layout.addWidget(regen_btn)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready — advertising pairing code")

    def _connect_console(self) -> None:
        console_type = self.console_combo.currentData()
        logger.info("Connect Console clicked: %s (stub)", console_type)
        self.status_display.setText(f"Connecting to {self.console_combo.currentText()} (stub)...")
        QMessageBox.information(self, _("Status"),
            f"Console connection (stub mode)\nType: {console_type}")

    def _open_plugins(self) -> None:
        logger.info("Plugins clicked (stub)")
        QMessageBox.information(self, _("Status"),
            "Console plugins:\n"
            "- Titan WebAPI\n- GrandMA3/2\n- ChamSys\n- ETC Eos\n- QLC+")

    def _regenerate_code(self) -> None:
        self.advertiser.stop()
        self.pairing_code = generate_pairing_code("light")
        self.advertiser = BLEAdvertiser("light", self.pairing_code)
        self.advertiser.start()
        self.code_display.setText(self.pairing_code)
        self.status_bar.showMessage(f"New code: {self.pairing_code}")

    def closeEvent(self, event) -> None:
        self.advertiser.stop()
        event.accept()


def main() -> None:
    lang = "en"
    set_language(lang)
    app = QApplication(sys.argv)
    window = LightWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

