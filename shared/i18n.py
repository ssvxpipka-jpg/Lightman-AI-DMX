"""
Lightman — internationalisation.

Public API:
    set_language(lang_code)   -> None
    get_language()            -> str
    tr(key)                   -> str  (translated or key fallback)
    TRANSLATIONS              -> dict[str, dict[str, str]]
"""

import logging

logger = logging.getLogger(__name__)

# Internal state
_CURRENT_LANG = "en"


TRANSLATIONS = {
    "en": {
        # Sidebar / navigation
        "studio": "Studio",
        "timeline": "Timeline",
        "script": "Script",
        "settings": "Settings",
        "rehearsals": "Rehearsals",
        "profile": "Profile",

        # Top bar
        "app_name": "Lightman",

        # Studio page
        "chat": "Assistant",
        "chat_placeholder": "AI chat will be available in the next build.",
        "chat_input_placeholder": "Ask the assistant…",
        "ai_coming_soon": "AI coming soon — this Beta build has no LLM connected.",
        "start_event": "▶ Start Event",
        "record": "⏺ Record",
        "stop": "⏹ Stop",
        "start": "▶ Start",
        "record_rehearsal": "⏺ Record Rehearsal",
        "stop_recording": "⏹ Stop Recording",
        "load_3d_model": "Load 3D Model",
        "save_scene": "Save Scene",
        "delete_scene": "Delete Scene",

        # Settings — AI provider
        "ai_provider": "AI Provider (BYOK)",
        "provider": "Provider:",
        "api_key": "API Key:",
        "api_key_placeholder": "Paste your API key here…",
        "base_url": "Base URL:",
        "model_name": "Model Name:",

        # Settings — Camera
        "camera_settings": "Camera Settings",
        "source": "Source:",
        "rtsp_url": "RTSP URL:",
        "hdmi_index": "HDMI Index:",
        "camera_position": "Camera Position:",
        "operator_notes": "Operator Notes:",
        "operator_notes_placeholder": "e.g. do not film left wing",

        # Settings — Lighting
        "lighting_mode": "Lighting Mode",
        "mode": "Mode:",
        "audience": "Audience:",
        "haze": "Enable Haze Analysis",
        "eco": "Eco Mode (reduce output)",
        "audience_kids": "Kids",
        "audience_teens": "Teens",
        "audience_adults": "Adults",
        "position_front": "Front",
        "position_balcony": "Balcony",
        "position_side_left": "Side Left",
        "position_side_right": "Side Right",
        "position_rear": "Rear",

        # Settings — Language
        "language": "Language",
        "interface_language": "Interface Language:",

        # Settings — Hotkeys
        "hotkeys": "Hotkeys",
        "hotkeys_desc": (
            "Click a shortcut field and press a key combination. "
            "Click 'Clear' to remove a shortcut."
        ),
        "action": "Action",
        "shortcut": "Shortcut",
        "save_hotkeys": "Save Hotkeys",
        "reset_defaults": "Reset to Defaults",

        # Settings — 3D scene
        "scene_management": "3D Scene Management",

        # Script page
        "show_script": "Show Script",
        "script_placeholder": "Write or paste your show script here…",
        "save_script": "Save Script",
        "load_script": "Load Script",
        "upload_txt": "Upload .txt",
        "upload_image": "Upload Image",
        "upload_video": "Upload Video",

        # Timeline page
        "show_timeline": "Show Timeline",
        "load_preset": "Load Show Preset (.json)",
        "save_preset": "Save Show Preset (.json)",
        "toggle_ai_follow": "Toggle AI Follow Mode",
        "ai_improvise": "Mode: AI Improvise",
        "ai_follow_preset": "Mode: AI Follow Preset",
        "timecode": "Timecode",
        "fixture": "Fixture",
        "value": "Value",
        "add_cue": "+ Add Cue",
        "remove_cue": "- Remove Cue",

        # Rehearsals page
        "rehearsal_session": "Rehearsal Session",
        "clear_log": "Clear Log",
        "export_log": "Export Log",
        "rehearsal_log": "Rehearsal Log",
        "rehearsal_log_placeholder": "Press Record to start logging the session…",

        # Profile page
        "user_profile": "User Profile",
        "account": "Account",
        "username": "Username:",
        "role": "Role:",
        "actions": "Actions",
        "logout": "Logout",
        "about": "About Lightman",
        "about_text": (
            "Lightman — Lighting control studio (Beta)\n\n"
            "• 3D scene: pyqtgraph.opengl\n"
            "• AI: not connected in this build\n"
            "• Hotkeys: configurable in Settings\n"
            "• Build: Beta visual"
        ),
        "role_operator": "Operator",

        # Login dialog
        "login_title": "Welcome to Lightman",
        "login_username_placeholder": "Username",
        "login_password_placeholder": "Password",
        "login": "Login",
        "register": "Register",
        "login_window_title": "Lightman — Login",
        "login_missing": "Enter username and password.",
        "login_missing_title": "Missing",
        "login_failed": "Login failed",
        "login_invalid": "Invalid credentials.",
        "login_error": "Login error",
        "register_ok": "User '{user}' created.",
        "register_exists": "User '{user}' exists.",
        "register_error": "Register error",
        "register_ok_title": "Registered",
        "register_exists_title": "Exists",

        # Status / messages
        "ready": "Ready",
        "event_started": "Event started.",
        "event_stopped": "Event stopped.",
        "blackout": "Blackout triggered.",
        "scene_saved": "Scene saved.",
        "scene_cleared": "Scene cleared.",
        "mode_set": "Mode: {mode}",
        "language_changed": "Language changed. Please restart the app to apply fully.",
        "language_changed_title": "Language",
        "hotkeys_saved": "Hotkeys saved and applied.",
        "hotkeys_reset": "Hotkeys reset to defaults.",
        "preset_saved": "Preset saved: {path}",
        "preset_loaded": "Preset loaded: {path}",
        "log_exported": "Log exported: {path}",
        "script_saved": "Script saved.",
        "no_script": "No saved script yet.",
        "recording_started": "▶ Recording started.",
        "recording_stopped": "■ Recording stopped.",
        "recording_rehearsal": "Recording rehearsal…",
        "rehearsal_stopped": "Rehearsal stopped.",
        "logout_hint": (
            "To log in as a different user, please restart the application."
        ),
        "save_failed": "Save failed",
        "load_failed": "Load failed",
        "delete_failed": "Delete failed",
        "export_failed": "Export failed",

        # Asset browser categories
        "moving_heads": "Moving Heads",
        "led_bars": "LED Bars",
        "lasers": "Lasers",
        "strobes": "Strobes",
        "dimmers": "Dimmers",
        "trusses_stands": "Trusses & Stands",
        "curtains": "Curtains",
        "other": "Other Fixtures",
        "search_placeholder": "Search…",
    },

    "ru": {
        # Sidebar / navigation
        "studio": "Студия",
        "timeline": "Таймлайн",
        "script": "Сценарий",
        "settings": "Настройки",
        "rehearsals": "Репетиции",
        "profile": "Профиль",

        # Top bar
        "app_name": "Lightman",

        # Studio page
        "chat": "Ассистент",
        "chat_placeholder": "ИИ-чат появится в следующей сборке.",
        "chat_input_placeholder": "Спросите ассистента…",
        "ai_coming_soon": "ИИ скоро — в этой Beta-сборке LLM не подключён.",
        "start_event": "▶ Начать шоу",
        "record": "⏺ Запись",
        "stop": "⏹ Стоп",
        "start": "▶ Старт",
        "record_rehearsal": "⏺ Записать репетицию",
        "stop_recording": "⏹ Остановить запись",
        "load_3d_model": "Загрузить 3D-модель",
        "save_scene": "Сохранить сцену",
        "delete_scene": "Удалить сцену",

        # Settings — AI provider
        "ai_provider": "ИИ-провайдер (BYOK)",
        "provider": "Провайдер:",
        "api_key": "API-ключ:",
        "api_key_placeholder": "Вставьте ваш API-ключ…",
        "base_url": "Базовый URL:",
        "model_name": "Название модели:",

        # Settings — Camera
        "camera_settings": "Настройки камеры",
        "source": "Источник:",
        "rtsp_url": "RTSP-адрес:",
        "hdmi_index": "HDMI-индекс:",
        "camera_position": "Позиция камеры:",
        "operator_notes": "Заметки оператора:",
        "operator_notes_placeholder": "напр. не снимать левое крыло",

        # Settings — Lighting
        "lighting_mode": "Режим освещения",
        "mode": "Режим:",
        "audience": "Аудитория:",
        "haze": "Включить анализ дымки",
        "eco": "Эко-режим (снизить яркость)",
        "audience_kids": "Дети",
        "audience_teens": "Подростки",
        "audience_adults": "Взрослые",
        "position_front": "Спереди",
        "position_balcony": "Балкон",
        "position_side_left": "Слева",
        "position_side_right": "Справа",
        "position_rear": "Сзади",

        # Settings — Language
        "language": "Язык",
        "interface_language": "Язык интерфейса:",

        # Settings — Hotkeys
        "hotkeys": "Горячие клавиши",
        "hotkeys_desc": (
            "Нажмите на поле и введите комбинацию клавиш. "
            "Кнопка 'Очистить' удаляет привязку."
        ),
        "action": "Действие",
        "shortcut": "Комбинация",
        "save_hotkeys": "Сохранить комбинации",
        "reset_defaults": "Сбросить по умолчанию",

        # Settings — 3D scene
        "scene_management": "Управление 3D-сценой",

        # Script page
        "show_script": "Сценарий шоу",
        "script_placeholder": "Напишите или вставьте сценарий здесь…",
        "save_script": "Сохранить сценарий",
        "load_script": "Загрузить сценарий",
        "upload_txt": "Загрузить .txt",
        "upload_image": "Загрузить изображение",
        "upload_video": "Загрузить видео",

        # Timeline page
        "show_timeline": "Таймлайн шоу",
        "load_preset": "Загрузить пресет (.json)",
        "save_preset": "Сохранить пресет (.json)",
        "toggle_ai_follow": "Переключить AI Follow",
        "ai_improvise": "Режим: ИИ импровизация",
        "ai_follow_preset": "Режим: ИИ следует пресету",
        "timecode": "Таймкод",
        "fixture": "Прибор",
        "value": "Значение",
        "add_cue": "+ Добавить cue",
        "remove_cue": "- Удалить cue",

        # Rehearsals page
        "rehearsal_session": "Сессия репетиции",
        "clear_log": "Очистить лог",
        "export_log": "Экспорт лога",
        "rehearsal_log": "Лог репетиции",
        "rehearsal_log_placeholder": "Нажмите Запись для старта логирования…",

        # Profile page
        "user_profile": "Профиль пользователя",
        "account": "Аккаунт",
        "username": "Имя:",
        "role": "Роль:",
        "actions": "Действия",
        "logout": "Выйти",
        "about": "О Lightman",
        "about_text": (
            "Lightman — студия управления светом (Beta)\n\n"
            "• 3D-сцена: pyqtgraph.opengl\n"
            "• ИИ: не подключён в этой сборке\n"
            "• Горячие клавиши: настраиваются в Настройках\n"
            "• Сборка: Beta visual"
        ),
        "role_operator": "Оператор",

        # Login dialog
        "login_title": "Добро пожаловать в Lightman",
        "login_username_placeholder": "Имя пользователя",
        "login_password_placeholder": "Пароль",
        "login": "Войти",
        "register": "Регистрация",
        "login_window_title": "Lightman — Вход",
        "login_missing": "Введите имя пользователя и пароль.",
        "login_missing_title": "Пропущено",
        "login_failed": "Вход не выполнен",
        "login_invalid": "Неверные учётные данные.",
        "login_error": "Ошибка входа",
        "register_ok": "Пользователь '{user}' создан.",
        "register_exists": "Пользователь '{user}' уже существует.",
        "register_error": "Ошибка регистрации",
        "register_ok_title": "Зарегистрировано",
        "register_exists_title": "Уже есть",

        # Status / messages
        "ready": "Готово",
        "event_started": "Шоу начато.",
        "event_stopped": "Шоу остановлено.",
        "blackout": "Блэкаут активирован.",
        "scene_saved": "Сцена сохранена.",
        "scene_cleared": "Сцена очищена.",
        "mode_set": "Режим: {mode}",
        "language_changed": "Язык изменён. Перезапустите приложение для полного применения.",
        "language_changed_title": "Язык",
        "hotkeys_saved": "Комбинации сохранены и применены.",
        "hotkeys_reset": "Комбинации сброшены по умолчанию.",
        "preset_saved": "Пресет сохранён: {path}",
        "preset_loaded": "Пресет загружен: {path}",
        "log_exported": "Лог экспортирован: {path}",
        "script_saved": "Сценарий сохранён.",
        "no_script": "Сохранённого сценария нет.",
        "recording_started": "▶ Запись начата.",
        "recording_stopped": "■ Запись остановлена.",
        "recording_rehearsal": "Запись репетиции…",
        "rehearsal_stopped": "Репетиция остановлена.",
        "logout_hint": "Для смены пользователя перезапустите приложение.",
        "save_failed": "Ошибка сохранения",
        "load_failed": "Ошибка загрузки",
        "delete_failed": "Ошибка удаления",
        "export_failed": "Ошибка экспорта",

        # Asset browser categories
        "moving_heads": "Вращающиеся головы",
        "led_bars": "LED-бары",
        "lasers": "Лазеры",
        "strobes": "Стробоскопы",
        "dimmers": "Диммеры",
        "trusses_stands": "Фермы и стойки",
        "curtains": "Занавесы",
        "other": "Прочие приборы",
        "search_placeholder": "Поиск…",
    },
}


def set_language(lang_code: str) -> None:
    global _CURRENT_LANG
    if lang_code in TRANSLATIONS:
        _CURRENT_LANG = lang_code
    else:
        logger.warning("Unknown language '%s', keeping '%s'.",
                       lang_code, _CURRENT_LANG)


def get_language() -> str:
    return _CURRENT_LANG


def tr(key: str, **kwargs) -> str:
    """
    Return translated string for `key` in the current language.
    Falls back to `key` if not found. Supports .format(**kwargs).
    """
    text = TRANSLATIONS.get(_CURRENT_LANG, {}).get(key)
    if text is None:
        text = TRANSLATIONS.get("en", {}).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text