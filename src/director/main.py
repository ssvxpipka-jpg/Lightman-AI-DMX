"""
Lightman Director — shell.

Layout:
    Top bar: app · blackout status · clock · ⚙ Settings
    Tabs: Director · Studio 3D · Timeline · Script · Rehearsals · Profile
    Bottom dock: Session Log

AI modes:
    easy   — AI proposes; user clicks ✅ to apply
    medium — AI applies; undo button appears for 10 s
    hard   — AI applies immediately, no undo

Blackout:
    Esc / ⬛ Blackout → LOCK: chat + settings + spawn blocked
    ▶ Resume → unlock
"""

import json
import os
import re
import sys
from datetime import datetime

from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QPushButton, QDialog, QLineEdit, QTextEdit,
    QMessageBox, QTabWidget, QGroupBox, QScrollArea, QComboBox,
    QTableWidget, QHeaderView, QDockWidget, QButtonGroup,
)

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from langchain_core.messages import HumanMessage  # noqa: E402

from shared.auth import (  # noqa: E402
    authenticate, register_user, ensure_default_user,
)
from shared.rag_init import train_knowledge_base  # noqa: E402
from shared.agents_config import build_graph  # noqa: E402


# ===========================================================================
# i18n
# ===========================================================================

_T = {
    "app_title": {"en": "Lightman", "ru": "Lightman"},
    "login": {"en": "Login", "ru": "Войти"},
    "register": {"en": "Register", "ru": "Регистрация"},
    "username": {"en": "Username", "ru": "Имя пользователя"},
    "password": {"en": "Password", "ru": "Пароль"},
    "login_missing": {"en": "Enter username and password.",
                      "ru": "Введите логин и пароль."},
    "login_invalid": {"en": "Invalid credentials.",
                      "ru": "Неверный логин или пароль."},
    "register_ok": {"en": "User created. You can log in now.",
                    "ru": "Пользователь создан. Войдите."},
    "register_exists": {"en": "Username already exists.",
                        "ru": "Пользователь уже существует."},
    "warning": {"en": "Warning", "ru": "Внимание"},
    "info": {"en": "Information", "ru": "Информация"},
    "settings": {"en": "Settings", "ru": "Настройки"},
    "ai_assistant": {"en": "AI Assistant", "ru": "ИИ-ассистент"},
    "session_log": {"en": "Session Log", "ru": "Журнал сеанса"},
    "ask_ai": {"en": "Ask the AI… (Enter to send)",
               "ru": "Спросите ИИ… (Enter — отправить)"},
    "you": {"en": "You", "ru": "Вы"},
    "ai": {"en": "AI", "ru": "ИИ"},
    "error": {"en": "Error", "ru": "Ошибка"},
    "clear": {"en": "Clear", "ru": "Очистить"},
    "no_api_key": {"en": "Set API key in Settings first.",
                   "ru": "Сначала задайте API-ключ в Настройках."},
    "tab_director": {"en": "Director", "ru": "Режиссёр"},
    "tab_studio": {"en": "Studio 3D", "ru": "Студия 3D"},
    "tab_timeline": {"en": "Timeline", "ru": "Таймлайн"},
    "tab_script": {"en": "Script", "ru": "Сценарий"},
    "tab_rehearsals": {"en": "Rehearsals", "ru": "Репетиции"},
    "tab_profile": {"en": "Profile", "ru": "Профиль"},
    "timeline_time": {"en": "Time", "ru": "Время"},
    "timeline_fixture": {"en": "Fixture", "ru": "Прибор"},
    "timeline_action": {"en": "Action", "ru": "Действие"},
    "timeline_intensity": {"en": "Intensity", "ru": "Интенсивность"},
    "script_placeholder": {"en": "Paste or write the show script here…",
                           "ru": "Вставьте или напишите сценарий шоу здесь…"},
    "rehearsals_placeholder": {"en": "Write rehearsal notes and logs here…",
                               "ru": "Пишите заметки и логи репетиций здесь…"},
    "profile_title": {"en": "Profile", "ru": "Профиль"},
    "profile_user": {"en": "User", "ru": "Пользователь"},
    "profile_role": {"en": "Role", "ru": "Роль"},
    "profile_role_admin": {"en": "Administrator", "ru": "Администратор"},
    "tab_ai": {"en": "AI Provider", "ru": "ИИ-провайдер"},
    "tab_ai_mode": {"en": "AI Mode", "ru": "Режим ИИ"},
    "tab_connections": {"en": "Connections", "ru": "Подключения"},
    "tab_language": {"en": "Language", "ru": "Язык"},
    "provider": {"en": "Provider", "ru": "Провайдер"},
    "api_key": {"en": "API Key", "ru": "API-ключ"},
    "base_url": {"en": "Base URL", "ru": "Базовый URL"},
    "model_name": {"en": "Model Name", "ru": "Модель"},
    "light_app_code": {"en": "Light App Code", "ru": "Код Light-приложения"},
    "sound_app_code": {"en": "Sound App Code", "ru": "Код Sound-приложения"},
    "language": {"en": "Language", "ru": "Язык"},
    "lang_en": {"en": "English", "ru": "Английский"},
    "lang_ru": {"en": "Russian", "ru": "Русский"},
    "save": {"en": "Save", "ru": "Сохранить"},
    "cancel": {"en": "Cancel", "ru": "Отмена"},
    "training": {"en": "AI Training", "ru": "Обучение ИИ"},
    "training_started": {"en": "Training started...",
                         "ru": "Обучение запущено..."},
    "training_done": {"en": "Training complete: %1 script chunks, %2 fixture chunks.",
                      "ru": "Обучение завершено: %1 чанков скрипта, %2 чанков фикстур."},
    "training_empty": {"en": "Training finished — no data found.",
                       "ru": "Обучение завершено — данные не найдены."},
    "blackout_active": {"en": "BLACKOUT — AI locked",
                        "ru": "БЛЭКАУТ — ИИ заблокирован"},
    "blackout_incomplete": {"en": "Blackout incomplete: some fixtures stuck. Lock NOT engaged.",
                            "ru": "Блэкаут неполный: приборы зависли. Блокировка НЕ включена."},
}

_LANG = "en"


def tr(key):
    entry = _T.get(key)
    if not entry:
        return key
    return entry.get(_LANG) or entry.get("en") or key


def set_language(lang):
    global _LANG
    if lang in ("en", "ru"):
        _LANG = lang


# ===========================================================================
# Scene-control markers + per-mode AI hints
# ===========================================================================

_SPAWN_RE = re.compile(r"\[SPAWN:\s*([^\]]+?)\]", re.IGNORECASE)
_REMOVE_RE = re.compile(r"\[REMOVE:\s*([^\]]+?)\]", re.IGNORECASE)

_SCENE_CONTROL_HINT = (
    "\n\n[Scene control]\n"
    "You can modify the 3D scene. To add a fixture, emit exactly "
    "[SPAWN: <fixture_name>]. To remove one, emit [REMOVE: <fixture_name>]. "
    "Use only fixture names that appear in the library.\n"
    "The markers are hidden from the user, but the actions may be executed "
    "depending on the current AI mode.\n\n"
    "[Laser safety — MANDATORY]\n"
    "The 'Dead zones' list above is a hard no-fly list. NEVER aim any "
    "laser or bright beam toward a dead zone's bounding box.\n\n"
    "[Blackout]\n"
    "If a blackout is active, you are FROZEN. Do not propose actions, "
    "do not suggest resuming. Only the operator can resume.\n"
)

_MODE_HINT = {
    "easy": (
        "\n[Mode: EASY]\n"
        "You are in suggestion mode. Emit [SPAWN:] / [REMOVE:] freely — "
        "the operator will confirm each action. Prefer explaining intent "
        "clearly before the markers.\n"
    ),
    "medium": (
        "\n[Mode: MEDIUM]\n"
        "Your actions are auto-applied with a 10-second undo window. "
        "Emit [SPAWN:] / [REMOVE:] for routine work, but avoid destructive "
        "moves unless clearly requested.\n"
    ),
    "hard": (
        "\n[Mode: HARD]\n"
        "Your actions apply IMMEDIATELY with no undo. Only emit "
        "[SPAWN:] / [REMOVE:] when you are certain. Double-check names. "
        "Never remove safety-critical items. Only Blackout can stop you.\n"
    ),
}


def _strip_markers(text):
    text = _SPAWN_RE.sub("", text)
    text = _REMOVE_RE.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ===========================================================================
# AutoTrainThread
# ===========================================================================

class AutoTrainThread(QThread):
    finished_train = Signal(str)

    SCRIPT_PATH = os.path.join(_PROJECT_ROOT, "data", "script.txt")
    FIXTURES_PATH = os.path.join(
        _PROJECT_ROOT, "fixtures_db", "fixtures_catalog.json"
    )

    def run(self):
        ts = tf = 0
        if os.path.isfile(self.SCRIPT_PATH):
            with open(self.SCRIPT_PATH, "r", encoding="utf-8") as fh:
                ts = train_knowledge_base(fh.read(), "script.txt")
        if os.path.isfile(self.FIXTURES_PATH):
            with open(self.FIXTURES_PATH, "r", encoding="utf-8") as fh:
                tf = train_knowledge_base(fh.read(), "fixtures.json")
        if ts == 0 and tf == 0:
            self.finished_train.emit(tr("training_empty"))
        else:
            self.finished_train.emit(
                tr("training_done").replace("%1", str(ts)).replace("%2", str(tf))
            )


# ===========================================================================
# ChatWorker — knows the AI mode and feeds it into the prompt + graph state
# ===========================================================================

class ChatWorker(QThread):
    reply_ready = Signal(str)
    error_occurred = Signal(str)
    spawn_requested = Signal(str)
    remove_requested = Signal(str)

    def __init__(self, question, settings, fixtures,
                 dead_zones=None, ai_mode="easy", parent=None):
        super().__init__(parent)
        self.question = question
        self.settings = dict(settings or {})
        self.settings["ai_mode"] = ai_mode
        self.fixtures = list(fixtures or [])
        self.dead_zones = list(dead_zones or [])
        self.ai_mode = ai_mode if ai_mode in _MODE_HINT else "easy"

    def _format_scene(self):
        if not self.fixtures:
            return "On-stage fixtures: (none)"
        lines = ["On-stage fixtures:"]
        for fx in self.fixtures:
            name = fx.get("name") or fx.get("type") or "fixture"
            pos = fx.get("position") or (0, 0, 0)
            att = fx.get("attached_to")
            suffix = f" [on {att}]" if att else ""
            inten = fx.get("intensity", 100)
            try:
                lines.append(
                    f"- {name} ({inten}%) at "
                    f"({float(pos[0]):.2f}, {float(pos[1]):.2f}, "
                    f"{float(pos[2]):.2f}){suffix}"
                )
            except (TypeError, ValueError, IndexError):
                lines.append(f"- {name} ({inten}%){suffix}")
        return "\n".join(lines)

    def _format_zones(self):
        if not self.dead_zones:
            return "Dead zones: (none)"
        lines = ["Dead zones — NEVER aim lasers or bright beams here:"]
        for z in self.dead_zones:
            name = z.get("name", "zone")
            pos = z.get("position", [0, 0, 0])
            size = z.get("size", [1, 1, 1])
            reason = z.get("reason", "")
            try:
                lines.append(
                    f"- {name} at ({float(pos[0]):.1f}, {float(pos[1]):.1f}, "
                    f"{float(pos[2]):.1f}), size "
                    f"{float(size[0]):.1f}×{float(size[1]):.1f}×"
                    f"{float(size[2]):.1f}. Reason: {reason}"
                )
            except (TypeError, ValueError, IndexError):
                lines.append(f"- {name}. Reason: {reason}")
        return "\n".join(lines)

    def _format_library(self):
        return ""

    def run(self):
        import traceback
        try:
            graph = build_graph()
            user_text = (
                f"{self._format_scene()}\n\n"
                f"{self._format_zones()}\n\n"
                f"{self._format_library()}\n"
                f"{_SCENE_CONTROL_HINT}\n"
                f"{_MODE_HINT[self.ai_mode]}\n"
                f"User question: {self.question}"
            )
            state = {
                "messages": [HumanMessage(content=user_text)],
                "settings": self.settings,
                "next": "director",
            }
            result = graph.invoke(state)
            messages = result.get("messages", [])
            raw = str(messages[-1].content) if messages else ""
            for name in _SPAWN_RE.findall(raw):
                self.spawn_requested.emit(name.strip())
            for name in _REMOVE_RE.findall(raw):
                self.remove_requested.emit(name.strip())
            self.reply_ready.emit(_strip_markers(raw))
        except Exception:
            traceback.print_exc()
            self.error_occurred.emit(traceback.format_exc())


# ===========================================================================
# LoginDialog
# ===========================================================================

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("login"))
        self.setMinimumWidth(400)
        title = QLabel(tr("app_title"))
        title.setObjectName("Title")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(tr("username"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(tr("password"))
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_btn = QPushButton(tr("login"))
        self.login_btn.setObjectName("Primary")
        self.register_btn = QPushButton(tr("register"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addSpacing(8)
        btns = QHBoxLayout()
        btns.addWidget(self.register_btn)
        btns.addStretch(1)
        btns.addWidget(self.login_btn)
        layout.addLayout(btns)

        self.login_btn.clicked.connect(self._on_login)
        self.register_btn.clicked.connect(self._on_register)
        self.password_input.returnPressed.connect(self._on_login)

    def _on_login(self):
        u = self.username_input.text().strip()
        p = self.password_input.text()
        if not u or not p:
            QMessageBox.warning(self, tr("warning"), tr("login_missing"))
            return
        if authenticate(u, p):
            self.accept()
        else:
            QMessageBox.warning(self, tr("warning"), tr("login_invalid"))

    def _on_register(self):
        u = self.username_input.text().strip()
        p = self.password_input.text()
        if not u or not p:
            QMessageBox.warning(self, tr("warning"), tr("login_missing"))
            return
        if register_user(u, p):
            QMessageBox.information(self, tr("info"), tr("register_ok"))
        else:
            QMessageBox.warning(self, tr("warning"), tr("register_exists"))


# ===========================================================================
# SettingsDialog — AI Provider / AI Mode / Connections / Language
# ===========================================================================

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = dict(settings or {})
        self.setWindowTitle(tr("settings"))
        self.setMinimumSize(720, 560)
        self.train_thread = None
        self.tabs = QTabWidget()

        # ============ TAB: AI PROVIDER ============
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "groq", "openrouter", "gemini", "mistral", "cerebras",
            "ollama_local", "lmstudio_local", "custom",
        ])
        self.provider_combo.setCurrentText(self.settings.get("provider", "groq"))
        self.api_key_input = QLineEdit(self.settings.get("api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.base_url_input = QLineEdit(self.settings.get("base_url", ""))
        self.model_input = QLineEdit(self.settings.get("model", ""))
        ai_form = QFormLayout()
        ai_form.setSpacing(10)
        ai_form.addRow(tr("provider") + ":", self.provider_combo)
        ai_form.addRow(tr("api_key") + ":", self.api_key_input)
        ai_form.addRow(tr("base_url") + ":", self.base_url_input)
        ai_form.addRow(tr("model_name") + ":", self.model_input)
        ai_group = QGroupBox(tr("tab_ai"))
        ai_group.setLayout(ai_form)
        self.tabs.addTab(self._wrap(ai_group), tr("tab_ai"))

        # ============ TAB: AI MODE ============
        self.ai_mode_group = QGroupBox(tr("tab_ai_mode"))
        mode_layout = QVBoxLayout(self.ai_mode_group)
        mode_layout.setSpacing(12)

        intro = QLabel(
            "Choose how autonomous the AI should be. "
            "The mode is injected into the AI prompt and controls how "
            "actions are applied. You can switch at any time."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #8a8a8a; padding-bottom: 8px;")
        mode_layout.addWidget(intro)

        self._mode_buttons = {}
        self._mode_button_group = QButtonGroup(self)
        self._mode_button_group.setExclusive(True)

        modes = [
            ("easy",   "🟢  EASY",
             "AI suggests — you decide. Buttons appear under each AI reply."),
            ("medium", "🟡  MEDIUM",
             "AI does routine work (spawn / remove). Undo button appears for 10 s."),
            ("hard",   "🔴  HARD",
             "AI applies immediately. No undo. Only Blackout can stop it."),
        ]
        current_mode = self.settings.get("ai_mode", "easy")
        for mode_key, title, description in modes:
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setMinimumHeight(64)
            btn.setStyleSheet(
                "QPushButton {"
                "  text-align: left;"
                "  padding: 12px 16px;"
                "  font-size: 13px;"
                "  border: 1px solid #303030;"
                "  border-radius: 6px;"
                "}"
                "QPushButton:checked {"
                "  border: 2px solid #ff8a00;"
                "  background-color: #2a2a2a;"
                "}"
                "QPushButton:hover {"
                "  background-color: #2a2a2a;"
                "}"
            )
            btn.setText(f"{title}\n{description}")
            btn.setChecked(mode_key == current_mode)
            self._mode_buttons[mode_key] = btn
            self._mode_button_group.addButton(btn)
            mode_layout.addWidget(btn)

        mode_layout.addStretch(1)
        self.tabs.addTab(self._wrap(self.ai_mode_group), tr("tab_ai_mode"))

        # ============ TAB: CONNECTIONS ============
        self.light_code_input = QLineEdit(self.settings.get("light_code", ""))
        self.light_code_input.setPlaceholderText("SL-LIGHT-XXXX")
        self.sound_code_input = QLineEdit(self.settings.get("sound_code", ""))
        self.sound_code_input.setPlaceholderText("SL-SOUND-XXXX")
        conn_form = QFormLayout()
        conn_form.setSpacing(10)
        conn_form.addRow(tr("light_app_code") + ":", self.light_code_input)
        conn_form.addRow(tr("sound_app_code") + ":", self.sound_code_input)
        conn_group = QGroupBox(tr("tab_connections"))
        conn_group.setLayout(conn_form)
        self.tabs.addTab(self._wrap(conn_group), tr("tab_connections"))

        # ============ TAB: LANGUAGE ============
        self.language_combo = QComboBox()
        self.language_combo.addItem(tr("lang_en"), "en")
        self.language_combo.addItem(tr("lang_ru"), "ru")
        idx = self.language_combo.findData(self.settings.get("language", _LANG))
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)
        lang_form = QFormLayout()
        lang_form.setSpacing(10)
        lang_form.addRow(tr("language") + ":", self.language_combo)
        lang_group = QGroupBox(tr("tab_language"))
        lang_group.setLayout(lang_form)
        self.tabs.addTab(self._wrap(lang_group), tr("tab_language"))

        # ============ BUTTONS ============
        save_btn = QPushButton(tr("save"))
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(self.tabs)
        layout.addLayout(btn_row)

    def _wrap(self, w):
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setWidget(w)
        return s

    def _selected_mode(self):
        for key, btn in self._mode_buttons.items():
            if btn.isChecked():
                return key
        return "easy"

    def _on_save(self):
        self.settings["provider"] = self.provider_combo.currentText()
        self.settings["api_key"] = self.api_key_input.text().strip()
        self.settings["base_url"] = self.base_url_input.text().strip()
        self.settings["model"] = self.model_input.text().strip()
        self.settings["ai_mode"] = self._selected_mode()
        self.settings["light_code"] = self.light_code_input.text().strip()
        self.settings["sound_code"] = self.sound_code_input.text().strip()
        self.settings["language"] = self.language_combo.currentData()

        os.makedirs(os.path.join(_PROJECT_ROOT, "data"), exist_ok=True)
        with open(os.path.join(_PROJECT_ROOT, "data", "settings.json"),
                  "w", encoding="utf-8") as fh:
            json.dump(self.settings, fh, indent=2)

        set_language(self.settings["language"])

        if self.settings["api_key"]:
            self.train_thread = AutoTrainThread(self)
            self.train_thread.finished_train.connect(
                lambda msg: QMessageBox.information(None, tr("training"), msg)
            )
            self.train_thread.start()
            QMessageBox.information(self, tr("training"), tr("training_started"))
        self.accept()


# ===========================================================================
# DirectorTab — chat + AI-mode-aware actions
# ===========================================================================

class DirectorTab(QWidget):
    spawn_requested = Signal(str)
    remove_requested = Signal(str)
    log_line = Signal(str)

    def __init__(self, settings_provider, fixtures_provider,
                 dead_zones_provider=None, blackout_provider=None,
                 ai_mode_provider=None, parent=None):
        super().__init__(parent)
        self.settings_provider = settings_provider
        self.fixtures_provider = fixtures_provider
        self.dead_zones_provider = dead_zones_provider or (lambda: [])
        self.blackout_provider = blackout_provider or (lambda: False)
        self.ai_mode_provider = ai_mode_provider or (lambda: "easy")
        self.worker = None
        self.pending_actions = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(tr("ai_assistant"))
        title.setObjectName("Section")
        header.addWidget(title)
        header.addStretch(1)

        self.mode_badge = QLabel("")
        self.mode_badge.setStyleSheet(
            "color: #ff8a00; padding: 2px 10px; "
            "border: 1px solid #ff8a00; border-radius: 10px; "
            "font-size: 11px; font-weight: bold;"
        )
        header.addWidget(self.mode_badge)

        clear_btn = QPushButton(tr("clear"))
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self._on_clear)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        layout.addWidget(self.history, 1)

        self.actions_widget = QWidget()
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(8)
        self.actions_layout.addStretch(1)
        self.actions_widget.setVisible(False)
        layout.addWidget(self.actions_widget)

        self.input = QLineEdit()
        self.input.setPlaceholderText(tr("ask_ai"))
        self.input.returnPressed.connect(self._on_send)
        layout.addWidget(self.input)

        self.refresh_mode_badge()

    def refresh_mode_badge(self):
        mode = self._current_mode().upper()
        colors = {"EASY": "#22c55e", "MEDIUM": "#f0a500", "HARD": "#ef4444"}
        color = colors.get(mode, "#8a8a8a")
        self.mode_badge.setText(f"● {mode}")
        self.mode_badge.setStyleSheet(
            f"color: {color}; padding: 2px 10px; "
            f"border: 1px solid {color}; border-radius: 10px; "
            f"font-size: 11px; font-weight: bold;"
        )

    def set_input_enabled(self, enabled):
        self.input.setEnabled(enabled)
        if not enabled:
            self.input.setPlaceholderText(
                "🔒 Blackout active — chat locked. Press Resume to unlock."
            )
        else:
            self.input.setPlaceholderText(tr("ask_ai"))

    def _current_mode(self):
        try:
            return self.ai_mode_provider() or "easy"
        except Exception:
            return "easy"

    def _on_clear(self):
        self.history.clear()
        self._clear_actions()

    def _clear_actions(self):
        while self.actions_layout.count() > 1:
            item = self.actions_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.actions_widget.setVisible(False)
        self.pending_actions = []

    def _on_send(self):
        if self.blackout_provider():
            self.log_line.emit(
                "<span style='color:#ef4444'>Chat blocked — blackout active</span>"
            )
            return
        question = self.input.text().strip()
        if not question:
            return
        if self.worker is not None and self.worker.isRunning():
            return
        self.input.clear()
        self._clear_actions()
        self.history.append(
            f"<p style='color:#ff8a00'><b>{tr('you')}:</b></p><p>{question}</p>"
        )
        self.log_line.emit(f"<span style='color:#ff8a00'>You:</span> {question}")

        settings = dict(self.settings_provider() or {})
        if not settings.get("api_key"):
            self.history.append(
                f"<p style='color:#ef4444'>{tr('no_api_key')}</p>")
            self.log_line.emit("<span style='color:#ef4444'>No API key</span>")
            return

        mode = self._current_mode()
        settings["ai_mode"] = mode

        fixtures = list(self.fixtures_provider() or [])
        zones = list(self.dead_zones_provider() or [])
        self.worker = ChatWorker(
            question, settings, fixtures, zones,
            ai_mode=mode, parent=self,
        )
        self.worker.reply_ready.connect(self._on_reply)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.spawn_requested.connect(self._on_spawn)
        self.worker.remove_requested.connect(self._on_remove)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
        self.log_line.emit(
            f"AI thinking… <span style='color:#8a8a8a'>(mode: {mode})</span>"
        )

    def _on_reply(self, text):
        self.history.append(
            f"<p style='color:#ff8a00'><b>{tr('ai')}:</b></p><p>{text}</p>")
        self.log_line.emit("<span style='color:#22c55e'>AI replied</span>")

    def _on_error(self, msg):
        self.history.append(
            f"<p style='color:#ef4444'><b>{tr('error')}:</b></p><p>{msg[:300]}</p>")
        self.log_line.emit("<span style='color:#ef4444'>AI error</span>")

    def _on_spawn(self, name):
        if self.blackout_provider():
            self.log_line.emit(
                f"<span style='color:#ef4444'>AI spawn blocked by blackout: {name}</span>"
            )
            return
        self._handle_action("spawn", name)

    def _on_remove(self, name):
        if self.blackout_provider():
            self.log_line.emit(
                f"<span style='color:#ef4444'>AI remove blocked by blackout: {name}</span>"
            )
            return
        self._handle_action("remove", name)

    def _handle_action(self, kind, name):
        mode = self._current_mode()
        label = "spawn" if kind == "spawn" else "remove"

        if mode == "hard":
            self.log_line.emit(
                f"<span style='color:#f0a500'>AI → {label}</span> {name} "
                f"<span style='color:#8a8a8a'>(hard mode)</span>"
            )
            if kind == "spawn":
                self.spawn_requested.emit(name)
            else:
                self.remove_requested.emit(name)
            return

        if mode == "medium":
            if kind == "spawn":
                self.spawn_requested.emit(name)
            else:
                self.remove_requested.emit(name)
            self._show_undo_button(kind, name)
            return

        self.pending_actions.append((kind, name))
        self._render_action_buttons()

    def _show_undo_button(self, kind, name):
        undo_btn = QPushButton(f"↩ Undo {kind}: {name}")
        undo_btn.setStyleSheet(
            "QPushButton { background-color: #3a2a1a; color: #ff9f26; "
            "border: 1px solid #5a3a1a; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #4a3a2a; }"
        )

        def _do_undo():
            self.log_line.emit(
                f"<span style='color:#ef4444'>Undo</span> {kind}: {name}"
            )
            if kind == "spawn":
                self.remove_requested.emit(name)
            else:
                self.spawn_requested.emit(name)
            undo_btn.deleteLater()

        undo_btn.clicked.connect(_do_undo)
        self.actions_layout.insertWidget(0, undo_btn)
        self.actions_widget.setVisible(True)
        QTimer.singleShot(10000, lambda: undo_btn.deleteLater())

    def _render_action_buttons(self):
        self._clear_actions()
        if not self.pending_actions:
            return

        for kind, name in self.pending_actions:
            btn = QPushButton(f"✅ {kind}: {name}")
            btn.setStyleSheet(
                "QPushButton { background-color: #1f3d2b; color: #4ade80; "
                "border: 1px solid #2b5c3f; padding: 6px 12px; border-radius: 4px; }"
                "QPushButton:hover { background-color: #2b5c3f; }"
            )

            def _apply(k=kind, n=name):
                self.log_line.emit(
                    f"<span style='color:#22c55e'>Apply</span> {k}: {n}"
                )
                if k == "spawn":
                    self.spawn_requested.emit(n)
                else:
                    self.remove_requested.emit(n)
                self.pending_actions = [
                    a for a in self.pending_actions if a != (k, n)
                ]
                self._render_action_buttons()

            btn.clicked.connect(_apply)
            self.actions_layout.insertWidget(
                self.actions_layout.count() - 1, btn
            )

        cancel_btn = QPushButton("❌ Cancel all")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #3a1a1a; color: #ef4444; "
            "border: 1px solid #5a2a2a; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #4a2a2a; }"
        )
        cancel_btn.clicked.connect(self._clear_actions)
        self.actions_layout.insertWidget(
            self.actions_layout.count() - 1, cancel_btn
        )
        self.actions_widget.setVisible(True)

    def _on_finished(self):
        self.worker = None


# ===========================================================================
# LogDock
# ===========================================================================

class LogDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(tr("session_log"), parent)
        self.setObjectName("LogDock")
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        toolbar = QHBoxLayout()
        toolbar.addStretch(1)
        clear_btn = QPushButton(tr("clear"))
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self._on_clear)
        toolbar.addWidget(clear_btn)
        copy_all_btn = QPushButton(tr("copy_all"))
        copy_all_btn.setMaximumWidth(100)
        copy_all_btn.clicked.connect(self._on_copy_all)
        toolbar.addWidget(copy_all_btn)
        layout.addLayout(toolbar)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text, 1)
        self.setWidget(container)

    def _on_clear(self):
        self.text.clear()

    def _on_copy_all(self):
        """Copy all log text to clipboard."""
        try:
            clipboard = self.text.parent().parent().window().clipboard()
            clipboard.setText(self.text.toPlainText())
        except Exception:
            pass

    def append(self, html):
        self.text.append(html)


class LogTab(QWidget):
    """A QWidget tab that displays session logs with Copy All functionality."""
    log_line = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        toolbar = QHBoxLayout()
        toolbar.addStretch(1)
        clear_btn = QPushButton(tr("clear"))
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self._on_clear)
        toolbar.addWidget(clear_btn)

        copy_all_btn = QPushButton(tr("copy_all"))
        copy_all_btn.setMaximumWidth(100)
        copy_all_btn.clicked.connect(self._on_copy_all)
        toolbar.addWidget(copy_all_btn)

        layout.addLayout(toolbar)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text, 1)

        self.log_line.connect(self.append)

    def _on_clear(self):
        self.text.clear()

    def _on_copy_all(self):
        """Copy all log text to clipboard."""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.text.toPlainText())
        except Exception:
            pass

    def append(self, html):
        self.text.append(html)


# ===========================================================================
# Simple tabs
# ===========================================================================

def _make_text_tab(placeholder):
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(24, 24, 24, 24)
    te = QTextEdit()
    te.setPlaceholderText(placeholder)
    layout.addWidget(te)
    return w


def _make_timeline_tab():
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(24, 24, 24, 24)
    table = QTableWidget(0, 4)
    table.setHorizontalHeaderLabels([
        tr("timeline_time"), tr("timeline_fixture"),
        tr("timeline_action"), tr("timeline_intensity"),
    ])
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    layout.addWidget(table)
    return w


def _make_profile_tab(username):
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(12)
    title = QLabel(tr("profile_title"))
    title.setObjectName("Section")
    layout.addWidget(title)
    form = QFormLayout()
    form.addRow(tr("profile_user") + ":", QLabel(username))
    form.addRow(tr("profile_role") + ":", QLabel(tr("profile_role_admin")))
    layout.addLayout(form)
    layout.addStretch(1)
    return w


# ===========================================================================
# MainWindow
# ===========================================================================

class MainWindow(QMainWindow):
    def __init__(self, settings, username="operator"):
        super().__init__()
        self.settings = dict(settings or {})
        self.username = username
        self.blackout_active = False
        self._saved_intensities = {}

        self.setWindowTitle(tr("app_title"))
        self.resize(1440, 900)

        # Studio3DPage FIRST — DirectorTab providers read from it
        try:
            self.studio = Studio3DPage()
        except Exception:
            import traceback
            traceback.print_exc()
            self.studio = QWidget()

        # ---------- central ----------
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------- top bar ----------
        topbar = QWidget()
        topbar.setObjectName("TopBar")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 10, 16, 10)
        tb.setSpacing(12)

        app_label = QLabel(tr("app_title"))
        app_label.setObjectName("Title")
        tb.addWidget(app_label)
        tb.addSpacing(24)

        self.blackout_status = QLabel("● Live")
        self.blackout_status.setStyleSheet("color: #22c55e;")
        tb.addWidget(self.blackout_status)

        tb.addStretch(1)

        self.clock_label = QLabel("--:--:--")
        self.clock_label.setStyleSheet("color: #8a8a8a; font-family: monospace;")
        tb.addWidget(self.clock_label)
        tb.addSpacing(12)

        self.blackout_btn = QPushButton("⬛ Blackout")
        self.blackout_btn.clicked.connect(self.toggle_blackout)
        tb.addWidget(self.blackout_btn)

        # ADD: BlenderDMX 3D Editor button
        self.blender_dmx_btn = QPushButton("Open BlenderDMX 3D Editor")
        self.blender_dmx_btn.clicked.connect(self._on_blender_dmx_triggered)
        tb.addWidget(self.blender_dmx_btn)

        self.settings_btn = QPushButton("⚙ " + tr("settings"))
        self.settings_btn.clicked.connect(self.open_settings)
        tb.addWidget(self.settings_btn)

        root.addWidget(topbar)

        # ---------- tabs ----------
        self.tabs = QTabWidget()
        self.director_tab = DirectorTab(
            settings_provider=lambda: self.settings,
            fixtures_provider=self._get_fixtures,
            dead_zones_provider=self._get_dead_zones,
            blackout_provider=lambda: self.blackout_active,
            ai_mode_provider=lambda: self.settings.get("ai_mode", "easy"),
        )
        self.director_tab.spawn_requested.connect(self._spawn_fixture)
        self.director_tab.remove_requested.connect(self._remove_fixture)

        self.tabs.addTab(self.director_tab, tr("tab_director"))
        self.tabs.addTab(self.studio, tr("tab_studio"))
        self.tabs.addTab(_make_timeline_tab(), tr("tab_timeline"))
        self.tabs.addTab(_make_text_tab(tr("script_placeholder")),
                         tr("tab_script"))
        self.tabs.addTab(_make_text_tab(tr("rehearsals_placeholder")),
                         tr("tab_rehearsals"))
        self.tabs.addTab(_make_profile_tab(self.username), tr("tab_profile"))
        root.addWidget(self.tabs, 1)

        self.setCentralWidget(central)

        # ---------- log tab ----------
        self.log_tab = LogTab(self)
        self.tabs.addTab(self.log_tab, tr("Logs"))
        self.director_tab.log_line.connect(self.log_tab.append)

        # ---------- clock ----------
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

        # ---------- Esc = blackout toggle ----------
        self._esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._esc.activated.connect(self.toggle_blackout)

        # ---------- boot log ----------
        self.log_tab.append(
            f"<span style='color:#8a8a8a'>Signed in as</span> {self.username}"
        )
        mode = self.settings.get("ai_mode", "easy")
        self.log_tab.append(
            f"<span style='color:#8a8a8a'>AI mode:</span> "
            f"<span style='color:#ff8a00'>{mode.upper()}</span>"
        )
        if not self.settings.get("api_key"):
            self.log_tab.append(
                "<span style='color:#f0a500'>Set API key in Settings to use AI</span>"
            )

    # -------------------------------------------------- view accessor
    def _view(self):
        """Find the Lightman3DView inside Studio3DPage, defensively."""
        for attr in ("view", "gl_view", "scene_view", "gl", "_view"):
            v = getattr(self.studio, attr, None)
            if v is not None and hasattr(v, "fixtures"):
                return v
        return None

    # -------------------------------------------------- data providers
    def _get_fixtures(self):
        v = self._view()
        if v is None:
            return []
        try:
            return list(v.fixtures)
        except Exception:
            return []

    def _get_dead_zones(self):
        v = self._view()
        if v is None:
            return []
        sd = getattr(v, "_scene_data", {})
        try:
            return list(sd.get("dead_zones", []))
        except Exception:
            return []

    # -------------------------------------------------- spawn / remove
    def _spawn_fixture(self, name):
        if self.blackout_active:
            self.log_tab.append(
                f"<span style='color:#ef4444'>Spawn blocked by blackout: {name}</span>"
            )
            return
        try:
            if hasattr(self.studio, "spawn_fixture_by_name"):
                self.studio.spawn_fixture_by_name(name)
                self.log_tab.append(
                    f"<span style='color:#22c55e'>Spawned</span> {name}"
                )
            else:
                self.log_tab.append(
                    "<span style='color:#ef4444'>Studio3DPage has no "
                    "spawn_fixture_by_name() — spawn skipped</span>"
                )
        except Exception as exc:
            self.log_tab.append(
                f"<span style='color:#ef4444'>Spawn failed:</span> {exc}"
            )

    def _remove_fixture(self, name):
        if self.blackout_active:
            self.log_tab.append(
                f"<span style='color:#ef4444'>Remove blocked by blackout: {name}</span>"
            )
            return
        try:
            if hasattr(self.studio, "remove_fixture_by_name"):
                self.studio.remove_fixture_by_name(name)
            else:
                v = self._view()
                if v is not None:
                    v.remove_fixture_by_name(name)
            self.log_tab.append(
                f"<span style='color:#f0a500'>Removed</span> {name}"
            )
        except Exception as exc:
            self.log_tab.append(
                f"<span style='color:#ef4444'>Remove failed:</span> {exc}"
            )

    # -------------------------------------------------- clock
    def _tick(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))

    # -------------------------------------------------- settings
    def open_settings(self):
        if self.blackout_active:
            self.log_tab.append(
                "<span style='color:#ef4444'>Settings blocked — blackout active</span>"
            )
            return
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() == QDialog.Accepted:
            self.settings = dlg.settings
            set_language(self.settings.get("language", _LANG))
            self.director_tab.refresh_mode_badge()
            self.log_tab.append(
                "<span style='color:#8a8a8a'>Settings saved — mode:</span> "
                f"<span style='color:#ff8a00'>"
                f"{self.settings.get('ai_mode', 'easy').upper()}</span>"
            )

    # -------------------------------------------------- blackout
    def toggle_blackout(self):
        if self.blackout_active:
            self._exit_blackout()
        else:
            self._enter_blackout()

    def _capture_intensities(self):
        v = self._view()
        saved = {}
        if v is None:
            return saved
        try:
            fixtures = list(v.fixtures)
        except Exception:
            return saved
        for fx in fixtures:
            name = fx.get("name")
            if not name:
                continue
            if fx.get("is_work_light") or fx.get("is_mount"):
                continue
            try:
                saved[name] = int(fx.get("intensity", 100))
            except Exception:
                saved[name] = 100
        return saved

    def _enter_blackout(self):
        v = self._view()
        if v is None:
            self.log_tab.append(
                "<span style='color:#ef4444'>Blackout failed: 3D view not found</span>"
            )
            return

        self._saved_intensities = self._capture_intensities()

        try:
            if hasattr(self.studio, "enter_blackout"):
                self.studio.enter_blackout()
            else:
                v.apply_blackout()
        except Exception:
            import traceback
            traceback.print_exc()
            self.log_tab.append(
                "<span style='color:#ef4444'>Blackout failed (exception)</span>"
            )
            return

        try:
            ok = v.verify_blackout()
        except Exception:
            ok = False

        if not ok:
            self.log_tab.append(
                f"<span style='color:#ef4444'>{tr('blackout_incomplete')}</span>"
            )
            return

        self.blackout_active = True
        self.director_tab.set_input_enabled(False)
        self.settings_btn.setEnabled(False)
        self.blackout_status.setText("● " + tr("blackout_active"))
        self.blackout_status.setStyleSheet("color: #ef4444;")
        self.blackout_btn.setText("▶ Resume")
        self.log_tab.append(
            f"<span style='color:#ef4444'><b>{tr('blackout_active')}</b></span>"
        )

    def _exit_blackout(self):
        v = self._view()
        try:
            if hasattr(self.studio, "exit_blackout"):
                self.studio.exit_blackout()
            elif v is not None:
                v.restore_intensities(self._saved_intensities)
        except Exception:
            import traceback
            traceback.print_exc()

        self.blackout_active = False
        self._saved_intensities = {}
        self.director_tab.set_input_enabled(True)
        self.settings_btn.setEnabled(True)
        self.blackout_status.setText("● Live")
        self.blackout_status.setStyleSheet("color: #22c55e;")
        self.blackout_btn.setText("⬛ Blackout")
        self.log_tab.append("<span style='color:#22c55e'>Resumed — live</span>")

    # -------------------------------------------------- BlenderDMX 3D Editor
    def _on_blender_dmx_triggered(self):
        """Export scene to MVR and launch bundled Blender with BlenderDMX."""
        try:
            from scripts.export_to_mvr import export_scene_to_mvr
        except ImportError:
            self.log_tab.append(
                "<span style='color:#ef4444'>BlenderDMX export: export_to_mvr module not found</span>"
            )
            return

        # Find bundled Blender
        blender_app = self._find_bundled_blender()
        if not blender_app:
            self.log_tab.append(
                "<span style='color:#ef4444'>Bundled Blender.app not found. "
                "Falling back to ui_3d.py (in-app 3D view).</span>"
            )
            return

        # Export scene to MVR
        scene_path = os.path.join(_PROJECT_ROOT, "data", "scene.json")
        if not os.path.isfile(scene_path):
            self.log_tab.append(
                "<span style='color:#ef4444'>scene.json not found — cannot export MVR</span>"
            )
            return

        try:
            with open(scene_path, "r", encoding="utf-8") as fh:
                scene_data = json.load(fh)
        except Exception as exc:
            self.log_tab.append(
                f"<span style='color:#ef4444'>Failed to read scene.json: {exc}</span>"
            )
            return

        mvr_path = os.path.join(_PROJECT_ROOT, "data", "exported_scene.mvr")
        try:
            export_scene_to_mvr(scene_data, mvr_path)
            self.log_tab.append(
                f"<span style='color:#22c55e'>Exported MVR to {mvr_path}</span>"
            )
        except Exception as exc:
            self.log_tab.append(
                f"<span style='color:#ef4444'>MVR export failed: {exc}</span>"
            )
            return

        # Launch Blender with BlenderDMX
        blender_exec = os.path.join(blender_app, "Contents", "MacOS", "Blender")
        if not os.path.isfile(blender_exec):
            self.log_tab.append(
                f"<span style='color:#ef4444'>Blender executable not found at {blender_exec}</span>"
            )
            return

        # Read version file
        version_file = os.path.join(blender_app, "Contents", "Resources", "blender_version.txt")
        blender_version = "unknown"
        if os.path.isfile(version_file):
            try:
                with open(version_file, "r") as fh:
                    blender_version = fh.read().strip()
            except Exception:
                pass

        # Build command: enable BlenderDMX and open MVR
        cmd = [
            blender_exec,
            "--python-expr",
            (
                "import bpy; "
                "bpy.ops.preferences.addon_enable(module='blenderdmx'); "
                "bpy.ops.wm.open_mainfile(filepath='" + mvr_path + "'); "
                "bpy.ops.wm.save_as_mainfile(filepath='" + mvr_path + "')"
            ),
        ]

        self.log_tab.append(
            f"<span style='color:#8a8a8a'>Launching Blender {blender_version} with BlenderDMX...</span>"
        )

        try:
            import subprocess
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            # Capture output asynchronously
            from PySide6.QtCore import QThread
            self._blender_proc = proc
            self._blender_log_thread = _BlenderLogReader(proc, self.log_tab)
            self._blender_log_thread.log_line.connect(self.log_tab.append)
            self._blender_log_thread.start()
        except Exception as exc:
            self.log_tab.append(
                f"<span style='color:#ef4444'>Failed to launch Blender: {exc}</span>"
            )

    def _find_bundled_blender(self):
        """Locate the bundled Blender.app in resources."""
        candidates = [
            os.path.join(_PROJECT_ROOT, "src", "director", "resources", "Blender.app"),
            os.path.join(_PROJECT_ROOT, "resources", "Blender.app"),
        ]
        for path in candidates:
            blender_exec = os.path.join(path, "Contents", "MacOS", "Blender")
            if os.path.isfile(blender_exec):
                return path
        return None


# ===========================================================================
# Blender log reader thread
# ===========================================================================

class _BlenderLogReader(QThread):
    """Reads stdout/stderr from a running Blender process and emits log lines."""
    log_line = Signal(str)

    def __init__(self, proc, log_dock, parent=None):
        super().__init__(parent)
        self._proc = proc
        self._log_dock = log_dock

    def run(self):
        try:
            for line in iter(self._proc.stdout.readline, ""):
                if not line:
                    break
                self.log_line.emit(f"<span style='color:#8a8a8a'>[Blender]</span> {line.rstrip()}")
            self._proc.stdout.close()
        except Exception:
            pass

        try:
            for line in iter(self._proc.stderr.readline, ""):
                if not line:
                    break
                self.log_line.emit(f"<span style='color:#ef4444'>[Blender]</span> {line.rstrip()}")
            self._proc.stderr.close()
        except Exception:
            pass

        self._proc.wait()


# ===========================================================================
# main()
# ===========================================================================

def _load_settings():
    path = os.path.join(_PROJECT_ROOT, "data", "settings.json")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}


def main():
    app = QApplication(sys.argv)
    try:
        ensure_default_user()
    except Exception:
        pass

    settings = _load_settings()
    set_language(settings.get("language", "en"))

    theme_path = os.path.join(_PROJECT_ROOT, "src", "director", "theme.qss")
    if os.path.isfile(theme_path):
        with open(theme_path, "r", encoding="utf-8") as fh:
            app.setStyleSheet(fh.read())

    # ── NEW: Auto-load fixtures catalog into RAG ────────────────────────
    fixtures_catalog = os.path.join(_PROJECT_ROOT, "data", "fixtures_catalog.json")
    if os.path.isfile(fixtures_catalog):
        print(f"Auto-loading fixtures catalog into RAG: {fixtures_catalog}")
        with open(fixtures_catalog, "r", encoding="utf-8") as fh:
            ts = train_knowledge_base(fh.read(), "fixtures_catalog")
        print(f"RAG trained with {ts} chunks from fixtures catalog")
    # └─────────────────────────────────────────────────────────────────────

    login = LoginDialog()
    if login.exec() != QDialog.Accepted:
        return 0

    username = login.username_input.text().strip() or "operator"
    win = MainWindow(settings, username=username)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())