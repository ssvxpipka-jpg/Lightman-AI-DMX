"""
Lightman Internationalization (i18n)
=====================================
Simple dictionary-based translation system.

Supported languages:
  - English ('en') — default
  - Russian ('ru')

Usage:
    from shared.i18n import _, set_language
    set_language('ru')
    text = _('Studio')  # Returns Russian translation if available
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from shared.config import get_logger

logger = get_logger("i18n")


# ─── Translation Data ──────────────────────────────────────────────────

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Director tabs
        "Studio": "Studio",
        "Settings": "Settings",
        "Script": "Script",
        "Live Light": "Live Light",
        "Knowledge Base": "Knowledge Base",
        "Rehearsals": "Rehearsals",
        "Profile": "Profile",

        # Window titles
        "Lightman Director": "Lightman Director",
        "Lightman Sound": "Lightman Sound",
        "Lightman Light": "Lightman Light",

        # Auth
        "Login": "Login",
        "Register": "Register",
        "Username": "Username",
        "Password": "Password",
        "New User? Register": "New User? Register",
        "Already have an account? Login": "Already have an account? Login",

        # Sound app
        "Start Audio": "Start Audio",
        "Audio Output": "Audio Output",
        "Loopback Device": "Loopback Device",
        "Grant Permission": "Grant Permission",
        "Status": "Status",

        # Light app
        "Connect Console": "Connect Console",
        "Console Status": "Console Status",
        "Console Type": "Console Type",

        # Settings tab
        "Mode": "Mode",
        "full_auto": "Full Auto",
        "assist": "Assist",
        "follow_only": "Follow Only",
        "Audience": "Audience",
        "kids": "Kids",
        "teens": "Teens",
        "adults": "Adults",
        "RTSP URL": "RTSP URL",
        "Standby Level": "Standby Level",
        "Intercept Threshold": "Intercept Threshold",
        "Language": "Language",
        "English": "English",
        "Russian": "Russian",

        # Server section
        "Lightman Server (Coming Soon)": "Lightman Server (Coming Soon)",
        "Server Login": "Server Login",
        "Server Password": "Server Password",
        "Connect": "Connect",
        "Server OS coming in v2.0": "Server OS coming in v2.0",

        # Profile
        "Display Name": "Display Name",
        "Save Profile": "Save Profile",

        # Live Light
        "No fixtures selected": "No fixtures selected",
        "Select Fixtures": "Select Fixtures",
        "Mute": "Mute",
        "Unmute": "Unmute",

        # Knowledge Base
        "Search": "Search",
        "Add Document": "Add Document",
        "No results": "No results found",

        # Rehearsals
        "Start Recording": "Start Recording",
        "Stop Recording": "Stop Recording",
        "Playback Speed": "Playback Speed",
        "Generate Report": "Generate Report",

        # Chat
        "Type a message...": "Type a message...",
        "Send": "Send",
        "Agent": "Agent",

        # Script
        "Parse Script": "Parse Script",
        "Timeline": "Timeline",
        "Scene": "Scene",
        "Action": "Action",

        # Console types
        "titan_webapi": "Titan WebAPI",
        "grandma3": "GrandMA3",
        "grandma2": "GrandMA2",
        "chamsys": "ChamSys",
        "etc_eos": "ETC Eos",
        "qlcplus": "QLC+",

        # Status messages
        "Connected": "Connected",
        "Disconnected": "Disconnected",
        "Starting": "Starting",
        "Stopped": "Stopped",
        "Error": "Error",
        "Ready": "Ready",
    },
    "ru": {
        # Director tabs
        "Studio": "Студио",
        "Settings": "Настройки",
        "Script": "Сценарий",
        "Live Light": "Прямой свет",
        "Knowledge Base": "База знаний",
        "Rehearsals": "Репетиции",
        "Profile": "Профиль",

        # Window titles
        "Lightman Director": "Lightman Дирижёр",
        "Lightman Sound": "Lightman Звук",
        "Lightman Light": "Lightman Свет",

        # Auth
        "Login": "Вход",
        "Register": "Регистрация",
        "Username": "Имя пользователя",
        "Password": "Пароль",
        "New User? Register": "Новый пользователь? Зарегистрироваться",
        "Already have an account? Login": "Уже есть аккаунт? Войти",

        # Sound app
        "Start Audio": "Запустить аудио",
        "Audio Output": "Аудио вывод",
        "Loopback Device": "Устройство loopback",
        "Grant Permission": "Разрешить",
        "Status": "Статус",

        # Light app
        "Connect Console": "Подключить консоль",
        "Console Status": "Статус консоли",
        "Console Type": "Тип консоли",

        # Settings tab
        "Mode": "Режим",
        "full_auto": "Полный автоном",
        "assist": "Помощь ИИ",
        "follow_only": "Только следование",
        "Audience": "Аудитория",
        "kids": "Дети",
        "teens": "Подростки",
        "adults": "Взрослые",
        "RTSP URL": "URL RTSP",
        "Standby Level": "Уровень ожидания",
        "Intercept Threshold": "Порог перехвата",
        "Language": "Язык",
        "English": "Английский",
        "Russian": "Русский",

        # Server section
        "Lightman Server (Coming Soon)": "Сервер Lightman (в скором времени)",
        "Server Login": "Логин сервера",
        "Server Password": "Пароль сервера",
        "Connect": "Подключить",
        "Server OS coming in v2.0": "Серверная ОС появится в v2.0",

        # Profile
        "Display Name": "Отображаемое имя",
        "Save Profile": "Сохранить профиль",

        # Live Light
        "No fixtures selected": "Фикстуры не выбраны",
        "Select Fixtures": "Выбрать фикстуры",
        "Mute": "Без звука",
        "Unmute": "Включить звук",

        # Knowledge Base
        "Search": "Поиск",
        "Add Document": "Добавить документ",
        "No results": "Результаты не найдены",

        # Rehearsals
        "Start Recording": "Начать запись",
        "Stop Recording": "Остановить запись",
        "Playback Speed": "Скорость воспроизведения",
        "Generate Report": "Сгенерировать отчёт",

        # Chat
        "Type a message...": "Введите сообщение...",
        "Send": "Отправить",
        "Agent": "Агент",

        # Script
        "Parse Script": "Разобрать сценарий",
        "Timeline": "Временная шкала",
        "Scene": "Сцена",
        "Action": "Действие",

        # Console types
        "titan_webapi": "Titan WebAPI",
        "grandma3": "GrandMA3",
        "grandma2": "GrandMA2",
        "chamsys": "ChamSys",
        "etc_eos": "ETC Eos",
        "qlcplus": "QLC+",

        # Status messages
        "Connected": "Подключено",
        "Disconnected": "Отключено",
        "Starting": "Запуск",
        "Stopped": "Остановлено",
        "Error": "Ошибка",
        "Ready": "Готово",
    },
}


# ─── Runtime State ───────────────────────────────────────────────────

_current_lang: str = "en"


def set_language(lang: str) -> None:
    """Set the current language. Falls back to 'en' if unsupported."""
    global _current_lang
    if lang not in _TRANSLATIONS:
        logger.warning("Language '%s' not supported, falling back to 'en'", lang)
        lang = "en"
    _current_lang = lang
    logger.info("Language set to: %s", lang)


def get_language() -> str:
    """Return the current language code."""
    return _current_lang


def _(key: str) -> str:
    """
    Translate a key to the current language.
    Falls back to the original key if no translation exists.
    """
    lang_dict = _TRANSLATIONS.get(_current_lang, _TRANSLATIONS["en"])
    return lang_dict.get(key, _TRANSLATIONS["en"].get(key, key))


def get_available_languages() -> list[tuple[str, str]]:
    """Return a list of (code, display_name) tuples for available languages."""
    display_names = {"en": "English", "ru": "Русский"}
    return [(code, display_names.get(code, code)) for code in _TRANSLATIONS.keys()]
