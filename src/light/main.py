"""
Lightman Light — OS-level console bridge.
"""

import os
import sys
import secrets
import pathlib
import logging

PROJECT_ROOT = str(pathlib.Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

THEME_PATH = os.path.join(PROJECT_ROOT, "src", "director", "theme.qss")
ICON_PATH = os.path.join(PROJECT_ROOT, "assets", "app_icon.png")

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QComboBox, QStatusBar,
    QMessageBox,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("light")

from shared.console_bridge import UniversalBridge

try:
    from shared.pairing import BLEAdvertiser  # type: ignore
    BLE_OK = True
except Exception as _e:  # pragma: no cover
    logger.warning("BLEAdvertiser unavailable: %s", _e)
    BLEAdvertiser = None
    BLE_OK = False


# OS → default port
OS_PORTS = {
    "Titan OS": 4430,
    "grandMA3 OS": 8000,
    "ChamSys OS": 8000,
    "ETC Eos OS": 8000,
    "QLC+ OS": 7700,
    "Mock OS": 0,
}


class LightWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lightman Light")
        self.resize(600, 720)

        self._code = f"SL-LIGHT-{secrets.token_hex(2).upper()}"
        self._bridge = None
        self._advertiser = None

        central = QWidget()
        self.setCentralWidget(central)
        v = QVBoxLayout(central)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        # Pairing code
        code_group = QGroupBox("Pairing Code")
        cg = QVBoxLayout(code_group)
        self.code_label = QLabel(self._code)
        self.code_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #4A9EFF;"
        )
        cg.addWidget(self.code_label)
        copy_btn = QPushButton("Copy Code")
        copy_btn.clicked.connect(self._copy_code)
        cg.addWidget(copy_btn)
        v.addWidget(code_group)

        # Console connection
        conn_group = QGroupBox("Console Connection")
        conn_v = QVBoxLayout(conn_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Operating System:"))
        self.os_combo = QComboBox()
        self.os_combo.addItems(list(OS_PORTS.keys()))
        row1.addWidget(self.os_combo, 1)
        conn_v.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("IP Address:"))
        self.ip_input = QLineEdit("127.0.0.1")
        row2.addWidget(self.ip_input, 1)
        conn_v.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("8000")
        row3.addWidget(self.port_input, 1)
        conn_v.addLayout(row3)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setCheckable(True)
        self.connect_btn.toggled.connect(self._toggle_connect)
        conn_v.addWidget(self.connect_btn)

        v.addWidget(conn_group)

        # Status
        status_group = QGroupBox("Status")
        sg = QVBoxLayout(status_group)
        self.status_label = QLabel("Disconnected")
        sg.addWidget(self.status_label)
        v.addWidget(status_group)

        # --- TEST MODE (REMOVE LATER) ---
        self.test_group = QGroupBox("Test Commands (Mock only)")
        tg = QVBoxLayout(self.test_group)
        for label in (
            "Blackout", "Strobe", "Brightness+", "Brightness-",
            "Blue LED", "Blue Fill",
        ):
            b = QPushButton(label)
            b.clicked.connect(
                lambda _checked=False, a=label: self._send_test(a)
            )
            tg.addWidget(b)
        self.test_group.setVisible(False)
        v.addWidget(self.test_group)
        # --- END TEST MODE ---

        v.addStretch(1)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

        self.os_combo.currentTextChanged.connect(self._on_os_changed)
        self._on_os_changed(self.os_combo.currentText())

        if BLE_OK and BLEAdvertiser is not None:
            self._advertiser = BLEAdvertiser(self._code)
            self._advertiser.start()
            logger.info("BLE advertiser started for %s", self._code)

    # ------------------------------------------------------------- helpers
    def _copy_code(self) -> None:
        QApplication.clipboard().setText(self._code)
        self.statusBar().showMessage("Pairing code copied")

    def _on_os_changed(self, os_name: str) -> None:
        default_port = OS_PORTS.get(os_name, 0)
        self.port_input.setText(str(default_port))

        # --- TEST MODE (REMOVE LATER) ---
        self.test_group.setVisible(os_name == "Mock OS")
        # --- END TEST MODE ---

    def _toggle_connect(self, on: bool) -> None:
        if on:
            os_name = self.os_combo.currentText()
            ip = self.ip_input.text().strip() or "127.0.0.1"
            try:
                port = int(self.port_input.text().strip() or "0")
            except ValueError:
                QMessageBox.warning(
                    self, "Invalid port", "Port must be a number."
                )
                self.connect_btn.setChecked(False)
                return

            self._bridge = UniversalBridge(
                console=os_name, ip=ip, port=port
            )
            self.status_label.setText(
                f"Connected: {os_name} @ {ip}:{port}"
            )
            self.connect_btn.setText("Disconnect")
            self.statusBar().showMessage(f"Connected to {os_name}")
        else:
            self._bridge = None
            self.status_label.setText("Disconnected")
            self.connect_btn.setText("Connect")
            self.statusBar().showMessage("Disconnected")

    # --- TEST MODE (REMOVE LATER) ---
    def _send_test(self, action: str) -> None:
        if self._bridge is None:
            QMessageBox.warning(
                self, "Not connected", "Click Connect first."
            )
            return
        self._bridge.send_command(action, 1)
        self.statusBar().showMessage(f"Sent: {action}")
    # --- END TEST MODE ---

    # ------------------------------------------------------------- close
    def closeEvent(self, event) -> None:
        if self._advertiser:
            self._advertiser.stop()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Lightman Light")

    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    if os.path.exists(THEME_PATH):
        with open(THEME_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        logger.info("Theme loaded: %s", THEME_PATH)
    else:
        logger.warning("theme.qss not found at %s", THEME_PATH)

    w = LightWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())