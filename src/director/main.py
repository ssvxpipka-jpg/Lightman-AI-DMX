"""Lightman Director — main application window."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from shared.agents_config import PROVIDER_PRESETS, build_graph
from shared.auth import authenticate, register_user, ensure_default_user
from shared.rag_init import train_knowledge_base

from src.director.ui_3d import Lightman3DView
from src.director.ui_asset_browser import AssetBrowserWidget

log = logging.getLogger(__name__)

SETTINGS_PATH = Path("data/settings.json")

SIDEBAR_ITEMS = ["Studio", "Timeline", "Script", "Rehearsals", "Profile"]

DEFAULT_SETTINGS: dict = {
    "ai_provider": "Custom",
    "ai_api_key": "",
    "ai_base_url": "",
    "ai_model": "",
    "camera_source": "IP",
    "camera_ip": "",
    "camera_port": "",
    "camera_position": "",
    "camera_notes": "",
    "lighting_mode": "Manual",
    "lighting_audience": "Front of House",
    "lighting_eco": False,
    "hotkey_start": "F5",
    "hotkey_stop": "F6",
    "hotkey_record": "Ctrl+Space",
    "language": "English",
}


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                merged = dict(DEFAULT_SETTINGS)
                merged.update(raw)
                return merged
        except (OSError, ValueError):
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ----------------------------------------------------------------------
# Chat worker — runs build_graph() in a background QThread (BYOK)
# ----------------------------------------------------------------------


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lightman — Login")
        self.setMinimumWidth(360)
        self.setModal(True)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)
        layout.addLayout(form)
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        buttons = QHBoxLayout()
        login_btn = QPushButton("Login")
        register_btn = QPushButton("Register")
        login_btn.clicked.connect(self._on_login)
        register_btn.clicked.connect(self._on_register)
        buttons.addWidget(login_btn)
        buttons.addWidget(register_btn)
        layout.addLayout(buttons)

    def _on_login(self):
        u = self.username_input.text().strip()
        p = self.password_input.text()
        if authenticate(u, p):
            self.accept()
        else:
            self.status_label.setText("Invalid credentials")
            self.status_label.setStyleSheet("color: #ff5555;")

    def _on_register(self):
        u = self.username_input.text().strip()
        p = self.password_input.text()
        if register_user(u, p):
            self.status_label.setText("Registered! Please log in.")
            self.status_label.setStyleSheet("color: #55ff55;")
        else:
            self.status_label.setText("User already exists")
            self.status_label.setStyleSheet("color: #ff5555;")


class ChatWorker(QThread):
    response = Signal(str)
    error = Signal(str)

    def __init__(self, settings: dict, user_input: str, history: list):
        super().__init__()
        self.settings = settings
        self.user_input = user_input
        self.history = history

    def run(self) -> None:
        graph = build_graph()
        state = {
            "user_input": self.user_input,
            "settings": self.settings,
            "history": list(self.history),
            "spatial": {},
        }
        result = graph.invoke(state)
        self.response.emit(result.get("response", ""))


class AutoTrainThread(QThread):
    """
    Trains the local ChromaDB knowledge base on the user's script and
    the fixtures catalogue.

    Triggered when the user saves a non-empty API key in the Settings
    dialog. Runs in a background thread so the UI never blocks, and emits
    `finished_train(msg)` on success or failure so the caller can pop a
    QMessageBox.
    """

    finished_train = Signal(str)

    SCRIPT_PATH = os.path.join("data", "script.txt")
    FIXTURES_PATH = os.path.join("fixtures_db", "fixtures_catalog.json")

    def run(self) -> None:
        try:
            trained_script = 0
            trained_fixtures = 0

            if os.path.isfile(self.SCRIPT_PATH):
                with open(self.SCRIPT_PATH, "r", encoding="utf-8") as handle:
                    script_text = handle.read()
                trained_script = train_knowledge_base(script_text, "script.txt")
                log.info(
                    "AutoTrainThread: %d script chunks", trained_script
                )
            else:
                log.info(
                    "AutoTrainThread: %s not found, skipping",
                    self.SCRIPT_PATH,
                )

            if os.path.isfile(self.FIXTURES_PATH):
                with open(self.FIXTURES_PATH, "r", encoding="utf-8") as handle:
                    fixtures_text = handle.read()
                trained_fixtures = train_knowledge_base(
                    fixtures_text, "fixtures.json"
                )
                log.info(
                    "AutoTrainThread: %d fixture chunks", trained_fixtures
                )
            else:
                log.info(
                    "AutoTrainThread: %s not found, skipping",
                    self.FIXTURES_PATH,
                )

            if trained_script == 0 and trained_fixtures == 0:
                self.finished_train.emit(
                    "AI training finished — no script or fixture data found."
                )
                return

            self.finished_train.emit(
                "AI successfully trained on script and fixtures."
            )

        except Exception as exc:
            log.exception("AutoTrainThread failed")
            self.finished_train.emit(f"AI training failed: {exc}")


# ----------------------------------------------------------------------
# Settings modal
# ----------------------------------------------------------------------


class SettingsDialog(QDialog):
    """Modal settings dialog with tabbed, scrollable pages."""

    def __init__(self, settings: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("⚙ Settings")
        self.setModal(True)
        self.resize(760, 620)
        self._settings = dict(settings)
        self._widgets: dict = {}
        self._build_ui()
        self._load_into_widgets()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self._tab_ai_provider()
        self._tab_camera()
        self._tab_lighting()
        self._tab_hotkeys()
        self._tab_scene()
        self._tab_language()

        btns = QHBoxLayout()
        btns.addStretch(1)
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        root.addLayout(btns)

    def _scroll_tab(self, title: str) -> QVBoxLayout:
        tab = QWidget()
        v = QVBoxLayout(tab)
        v.setContentsMargins(8, 8, 8, 8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cv = QVBoxLayout(content)
        cv.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(content)
        v.addWidget(scroll)
        self.tabs.addTab(tab, title)
        return cv

    def _group(self, layout, title: str) -> QGroupBox:
        gb = QGroupBox(title)
        gb.setLayout(layout)
        layout.addWidget(gb)
        layout.addStretch(1)
        return gb

    def _field(self, layout, label: str, widget, key: str) -> None:
        layout.addRow(label, widget)
        self._widgets[key] = widget

    def _tab_ai_provider(self) -> None:
        cv = self._scroll_tab("AI Provider")
        form = QFormLayout()
        self._group(form, "AI Provider")

        provider = QComboBox()
        provider.addItems(list(PROVIDER_PRESETS.keys()) + ["Custom"])
        self._field(form, "Provider", provider, "ai_provider")

        api_key = QLineEdit()
        api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input = api_key
        self._field(form, "API Key", api_key, "ai_api_key")

        base_url = QLineEdit()
        self._field(form, "Base URL", base_url, "ai_base_url")

        model = QLineEdit()
        self._field(form, "Model Name", model, "ai_model")

    def _tab_camera(self) -> None:
        cv = self._scroll_tab("Camera")
        form = QFormLayout()
        self._group(form, "Camera Source")

        source = QComboBox()
        source.addItems(["IP", "HDMI"])
        self._field(form, "Source", source, "camera_source")

        ip = QLineEdit()
        self._field(form, "IP / URL", ip, "camera_ip")

        port = QLineEdit()
        self._field(form, "Port", port, "camera_port")

        position = QLineEdit()
        self._field(form, "Position", position, "camera_position")

        notes = QLineEdit()
        self._field(form, "Notes", notes, "camera_notes")

    def _tab_lighting(self) -> None:
        cv = self._scroll_tab("Lighting")
        form = QFormLayout()
        self._group(form, "Lighting")

        mode = QComboBox()
        mode.addItems(["Manual", "Auto", "Music", "Timecode"])
        self._field(form, "Mode", mode, "lighting_mode")

        audience = QComboBox()
        audience.addItems(["Front of House", "Stage", "Audience", "All"])
        self._field(form, "Audience", audience, "lighting_audience")

        eco_cb = QCheckBox("Eco Mode")
        self._field(form, "Eco Mode", eco_cb, "lighting_eco")

    def _tab_hotkeys(self) -> None:
        cv = self._scroll_tab("Hotkeys")
        form = QFormLayout()
        self._group(form, "Hotkeys")

        for key, label in [
            ("hotkey_start", "Start"),
            ("hotkey_stop", "Stop"),
            ("hotkey_record", "Record"),
        ]:
            edit = QKeySequenceEdit()
            edit.setKeySequence(QKeySequence(self._settings.get(key, "")))
            self._field(form, label, edit, key)

    def _tab_scene(self) -> None:
        cv = self._scroll_tab("Scene")
        form = QFormLayout()
        self._group(form, "Scene")

        path_edit = QLineEdit(str(SETTINGS_PATH))
        self._field(form, "Settings path", path_edit, "settings_path")

    def _tab_language(self) -> None:
        cv = self._scroll_tab("Language")
        form = QFormLayout()
        self._group(form, "Language")

        lang = QComboBox()
        lang.addItems(["Russian", "English"])
        self._field(form, "Language", lang, "language")

    def _load_into_widgets(self) -> None:
        for key, widget in self._widgets.items():
            value = self._settings.get(key, "")
            if widget is None:
                continue
            if isinstance(widget, QComboBox):
                idx = widget.findText(str(value), Qt.MatchFixedString)
                if idx < 0:
                    idx = 0
                widget.setCurrentIndex(idx)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QKeySequenceEdit):
                widget.setKeySequence(QKeySequence(str(value)))
            else:
                widget.setText(str(value))

    def _on_save(self) -> None:
        for key, widget in self._widgets.items():
            if widget is None:
                continue
            if isinstance(widget, QComboBox):
                self._settings[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                self._settings[key] = widget.isChecked()
            elif isinstance(widget, QKeySequenceEdit):
                seq = widget.keySequence()
                self._settings[key] = seq.toString() if not seq.isEmpty() else ""
            else:
                self._settings[key] = widget.text()
        save_settings(self._settings)

    def accept(self) -> None:
        api_key = self.api_key_input.text().strip()

        # Persist settings from every tab.
        self._on_save()

        # Make the API key visible to the rest of the app before training starts.
        self._settings["ai_api_key"] = api_key
        self.settings = dict(self._settings)

        # Trigger local RAG auto-training when a non-empty API key is provided.
        if api_key:
            self.train_thread = AutoTrainThread()
            self.train_thread.finished_train.connect(
                lambda msg: QMessageBox.information(self, "AI Training", msg)
            )
            self.train_thread.start()

        super().accept()

    def settings(self) -> dict:
        return self._settings



# ----------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lightman")
        self.resize(1400, 900)

        self._settings = load_settings()
        self._chat_history: list = []
        self._worker: ChatWorker | None = None

        self._build_ui()
        self._start_clock()

        # Data binding: asset browser -> 3D view
        self.asset_browser.fixture_selected.connect(
            self.view_3d.spawn_fixture_on_stage
        )

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top = QWidget()
        top.setFixedHeight(46)
        top.setObjectName("topBar")
        tlayout = QHBoxLayout(top)
        tlayout.setContentsMargins(12, 0, 12, 0)

        title = QLabel("Lightman")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet("font-family: monospace;")

        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self._open_settings)

        tlayout.addWidget(title)
        tlayout.addStretch(1)
        tlayout.addWidget(self.clock_lbl)
        tlayout.addWidget(self.settings_btn)
        root.addWidget(top)

        main_split = QSplitter()
        main_split.setChildrenCollapsible(False)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for item_text in SIDEBAR_ITEMS:
            self.sidebar.addItem(QListWidgetItem(item_text))
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        main_split.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self._build_pages()
        main_split.addWidget(self.stack)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)

        root.addWidget(main_split, 1)

    def _build_pages(self) -> None:
        self.stack.addWidget(self._build_studio_page())
        for _ in range(4):
            page = QWidget()
            page.setObjectName("placeholderPage")
            self.stack.addWidget(page)

    def _build_studio_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(6)

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)

        chat_widget = QWidget()
        cv = QVBoxLayout(chat_widget)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.addWidget(QLabel("AI Chat"))
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        cv.addWidget(self.chat_history, 1)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask the lighting AI…")
        self.chat_input.returnPressed.connect(self._on_chat_enter)
        cv.addWidget(self.chat_input)

        self.view_3d = Lightman3DView()

        self.asset_browser = AssetBrowserWidget()

        splitter.addWidget(chat_widget)
        splitter.addWidget(self.view_3d)
        splitter.addWidget(self.asset_browser)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        v.addWidget(splitter, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.btn_start = QPushButton("▶ Start")
        self.btn_record = QPushButton("⏺ Record")
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_start.clicked.connect(self._on_start)
        self.btn_record.clicked.connect(self._on_record)
        self.btn_stop.clicked.connect(self._on_stop)
        bottom.addWidget(self.btn_start)
        bottom.addWidget(self.btn_record)
        bottom.addWidget(self.btn_stop)
        v.addLayout(bottom)

        return page

    def _start_clock(self) -> None:
        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self) -> None:
        self.clock_lbl.setText(datetime.now().strftime("%H:%M:%S"))

    def _on_sidebar_changed(self, row: int) -> None:
        if 0 <= row < self.stack.count():
            self.stack.setCurrentRow(row)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        if dlg.exec():
            self._settings = dlg.settings()

    def _on_chat_enter(self) -> None:
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_input.clear()
        self._chat_history.append({"role": "user", "content": text})
        self.chat_history.append(f'<p style="color:#cfcfdf"><b>You:</b> {text}</p>')
        self.chat_history.append(
            '<p style="color:#8f8f9f"><i>AI is thinking…</i></p>'
        )

        self._worker = ChatWorker(self._settings, text, self._chat_history)
        self._worker.response.connect(self._on_chat_response)
        self._worker.error.connect(self._on_chat_error)
        self._worker.start()

    def _on_chat_response(self, response: str) -> None:
        self._chat_history.append({"role": "assistant", "content": response})
        self.chat_history.append(
            f'<p style="color:#a5d6ff"><b>AI:</b> {response}</p>'
        )
        self.chat_history.append("<hr>")

    def _on_chat_error(self, message: str) -> None:
        self.chat_history.append(
            f'<p style="color:#ff8a80"><b>AI error:</b> {message}</p>'
        )
        self.chat_history.append("<hr>")

    def _on_start(self) -> None:
        self.statusBar().showMessage("Started", 2500)

    def _on_record(self) -> None:
        self.statusBar().showMessage("Recording", 2500)

    def _on_stop(self) -> None:
        self.statusBar().showMessage("Stopped", 2500)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    theme_path = os.path.join(os.path.dirname(__file__), "theme.qss")
    if os.path.exists(theme_path):
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    ensure_default_user()
    login = LoginDialog()
    if login.exec() != QDialog.Accepted:
        return 0
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

