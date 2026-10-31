"""
Lightman Sound — audio capture and OSC sender (Director IP + Port).
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

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QStatusBar, QMessageBox,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sound")

from shared.osc_bridge import OSCClient

try:
    from shared.audio_source import AudioAnalyzer  # type: ignore
    AUDIO_OK = True
except Exception as _e:  # pragma: no cover
    logger.warning("AudioAnalyzer unavailable: %s", _e)
    AudioAnalyzer = None
    AUDIO_OK = False

try:
    from shared.pairing import BLEAdvertiser  # type: ignore
    BLE_OK = True
except Exception as _e:  # pragma: no cover
    logger.warning("BLEAdvertiser unavailable: %s", _e)
    BLEAdvertiser = None
    BLE_OK = False


class SoundWindow(QMainWindow):
    bpm_signal = Signal(float)
    beat_signal = Signal(int)
    energy_signal = Signal(float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lightman Sound")
        self.resize(600, 580)

        self._code = f"SL-SOUND-{secrets.token_hex(2).upper()}"
        self._osc = None
        self._analyzer = None
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

        # Director connection
        conn_group = QGroupBox("Director Connection")
        conn_v = QVBoxLayout(conn_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Director IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        row1.addWidget(self.ip_input, 1)
        conn_v.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("8000")
        row2.addWidget(self.port_input, 1)
        conn_v.addLayout(row2)

        self.capture_btn = QPushButton("Start Audio Capture")
        self.capture_btn.setCheckable(True)
        self.capture_btn.toggled.connect(self._toggle_capture)
        conn_v.addWidget(self.capture_btn)

        v.addWidget(conn_group)

        # Status
        status_group = QGroupBox("Status")
        sg = QVBoxLayout(status_group)
        self.status_label = QLabel("Idle")
        sg.addWidget(self.status_label)
        self.bpm_label = QLabel("BPM: —")
        sg.addWidget(self.bpm_label)
        self.energy_label = QLabel("Energy: —")
        sg.addWidget(self.energy_label)
        v.addWidget(status_group)

        v.addStretch(1)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

        self.bpm_signal.connect(self._apply_bpm)
        self.beat_signal.connect(self._apply_beat)
        self.energy_signal.connect(self._apply_energy)

        if BLE_OK and BLEAdvertiser is not None:
            self._advertiser = BLEAdvertiser(self._code)
            self._advertiser.start()
            logger.info("BLE advertiser started for %s", self._code)

    # ------------------------------------------------------------- helpers
    def _copy_code(self) -> None:
        QApplication.clipboard().setText(self._code)
        self.statusBar().showMessage("Pairing code copied")

    def _toggle_capture(self, on: bool) -> None:
        if on:
            ip = self.ip_input.text().strip()
            try:
                port = int(self.port_input.text().strip() or "8000")
            except ValueError:
                QMessageBox.warning(
                    self, "Invalid port", "Port must be a number."
                )
                self.capture_btn.setChecked(False)
                return

            if not ip:
                QMessageBox.warning(self, "Missing", "Enter Director IP.")
                self.capture_btn.setChecked(False)
                return

            self._osc = OSCClient(ip=ip, port=port)

            if AUDIO_OK and AudioAnalyzer is not None:
                self._analyzer = AudioAnalyzer(
                    on_bpm=lambda v: self.bpm_signal.emit(float(v)),
                    on_beat=lambda i: self.beat_signal.emit(int(i)),
                    on_energy=lambda v: self.energy_signal.emit(float(v)),
                )
                self._analyzer.start()

            self.status_label.setText(
                f"Capturing on {sys.platform} → {ip}:{port}"
            )
            self.capture_btn.setText("Stop Audio Capture")
            self.statusBar().showMessage("Audio capture started")
        else:
            if self._analyzer:
                self._analyzer.stop()
                self._analyzer = None
            self.status_label.setText("Idle")
            self.capture_btn.setText("Start Audio Capture")
            self.statusBar().showMessage("Audio capture stopped")

    # ------------------------------------------------------------- callbacks
    def _apply_bpm(self, bpm: float) -> None:
        self.bpm_label.setText(f"BPM: {bpm:.1f}")
        if self._osc:
            self._osc.send_bpm(bpm)

    def _apply_beat(self, idx: int) -> None:
        if self._osc:
            self._osc.send_beat(idx)

    def _apply_energy(self, energy: float) -> None:
        self.energy_label.setText(f"Energy: {energy:.3f}")
        if self._osc:
            self._osc.send_energy(energy)

    # ------------------------------------------------------------- close
    def closeEvent(self, event) -> None:
        if self._analyzer:
            self._analyzer.stop()
        if self._advertiser:
            self._advertiser.stop()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Lightman Sound")

    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    if os.path.exists(THEME_PATH):
        with open(THEME_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        logger.info("Theme loaded: %s", THEME_PATH)
    else:
        logger.warning("theme.qss not found at %s", THEME_PATH)

    w = SoundWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())