# Lightman AI DMX

**AI-ассистент для ОС пульта (Titan, grandMA3, EOS). Open-source, local-first.**
**AI assistant for console OS. Open-source, local-first stage lighting control.**

[**⬇ Скачать последний релиз**](https://github.com/ssvxpipka-jpg/Lightman-AI-DMX/releases/latest) | [**❤️ Поддержать проект (DonationAlerts)**](https://www.donationalerts.com/r/afe1g)

Lightman — это не замена консоли, а интеллектуальный слой поверх неё. Он видит 3D-сцену через встроенный BlenderDMX, понимает DMX-протоколы (Art-Net, sACN, OSC) и помогает световику, работая локально без телеметрии.

### ✨ Фичи
- **AI Director (BYOK)**: Подключение Groq, OpenRouter, Gemini, Mistral, Cerebras.
- **BlenderDMX 3D Studio**: Встроенный Blender с аддоном BlenderDMX (Universal2 для macOS).
- **EpocCam Vision**: Компьютерное зрение через веб-камеру (трекинг актеров, анализ лучей, оценка плотности дыма/Haze).
- **Local RAG Knowledge Base**: База знаний на 300+ приборов и DMX-протоколы (ChromaDB), работает полностью локально.
- **Absolute Blackout**: Жесткий LOCK (ИИ не может отменить, дежурный свет 2%).
- **Console OS Integration**: Подключение к ОС пультов (Titan, grandMA3, EOS) по IP.

### 🎛️ DMX Channel Configuration

Lightman uses fixture definition data from `fixtures_db/fixtures_catalog.json` to map DMX channels. Each fixture entry includes:

- `dmx_channels` — количество DMX каналов (обычно 2–12 шт)
- `type` — тип прибора (spot/wash/beam), определяет default channel layout
- `modes` — режимы работы (например, `1ch`, `2ch`, `12ch`)

**How to set/channel configure:**

1. **Through fixture catalog**: Edit `fixtures_db/fixtures_catalog.json` — modify `dmx_channels` and `modes` for any fixture
2. **Through BlenderDMX addon**: The addon reads fixture data and auto-generates channel mappings
3. **OSC mapping** (optional): Lightman sends `/lightman/bpm`, `/lightman/beat`, `/lightman/energy` — these can map to console channels via custom OSC routing

**Typical DMX channel layout per fixture type:**

| Fixture Type | Channels | Functions |
|---|---|---|
| **Spot/Beam** (e.g., Sharpy) | 2–4 | Red, Green, Blue, Gobo/Strobe |
| **Wash** (e.g., LED Wash) | 8–12 | RGB, Dimmer, Strobe, Zoom, Focus |
| **PAR** | 3–4 | Red, Green, Blue, Master Dimmer |

**Control methods:**

- **DMX universes** — через BlenderDMX addon + физический DMX интерфейс
- **Art-Net/sACN** — сетевой протокол для профессиональных консолей (Titan, grandMA3)
- **OSC** — Lightman шлет `/lightman/bpm`, `/lightman/beat`, `/lightman/energy` по UDP

**Для интеграции с Titan/GrandMA:**
Настройте адреса OSC в `shared/osc_bridge.py` под формат вашей консоли, либо используйте DMX шлюз между Lightman и сетью консоли.
Проект распространяется по лицензии **MIT**. Мы используем модель **Open Core**:
- **v1.x – v3.x (Бесплатно навсегда)**: Ядро системы, AI-директор, 3D-редактор и базовые интеграции доступны всем бесплатно без ограничений.
- **v4.0+ (Платные модули)**: Начиная с 4-й версии, мы планируем добавлять сложные корпоративные модули (расширенный AI-резерв для больших площадок, трекинг, интеркомы) по платной подписке. Базовое ядро останется открытым.

### 🗺️ Roadmap (Планы)
- **v1.1.1 (Текущий релиз)**: Интеграция BlenderDMX, EpocCam Vision, логи в UI, фиолетовая тема. *(Известный баг: старая вкладка 3D осталась в UI, будет убрана в v1.1.2).*
- **v1.1.2**: Удаление старой вкладки 3D, добавление полной библиотеки из 300+ приборов в UI (Drag & Drop), дым-машины.
- **v1.2.0**: Multi-agent система (ИИ-агенты для звука, света, блэкаута), авто-калибровка лучей.
- **v2.0.0**: Серверная ОС для Llama (локальный ИИ на отдельном железе), трекинг через админ-панель, поддержка USB-пультов.

### 🚀 Установка (Простое руководство)

**Как установить Lightman:**

1. **Скачай последнюю версию:**
   Зайди по ссылке: https://github.com/ssvxpipka-jpg/Lightman-AI-DMX/releases/latest
   Скачай файл под свою операционную систему:
   - **Windows:** `Lightman-windows.exe` (инсталлятор)
   - **macOS:** `Lightman-macOS.dmg` (архив)

2. **Установи программу:**

   **Windows:**
   - Дважды кликни по скачанному файлу `Lightman.exe`
   - Нажми "Next" → "I Agree" → "Install"
   - Готово! Lightman появится в меню Пуск

   **macOS:**
   - Открой скачанный `.dmg` файл
   - Перетащи иконку Lightman в папку Applications
   - Нажми правой кнопкой на иконку в Applications → "Открыть" (только первый раз для обхода Gatekeeper)
   - Lightman появится в Launchpad


3. **Запусти Lightman:**
   - Найди иконку в меню Пуск (Windows) или Launchpad (macOS)
   - Нажми на неё
   - Программа сама найдет подключенное DMX-оборудование
   - Начинай управлять светом!

**Если программа не запускается:**
- **Windows:** Нажми "Все равно запустить" при предупреждении от Windows
- **macOS:** Системные настройки → Общие → "Открыть все равно" рядом с Lightman

### 🏷️ Topics (Теги для поиска)
`ai` `stage-lighting` `dmx` `lighting-control` `pyside6` `langgraph` `chromadb` `blenderdmx` `opencv` `macos` `windows` `linux` `open-source` `byok` `theatre-tech` `epoccam`

---
[**❤️ Поддержать проект (DonationAlerts)**](https://www.donationalerts.com/r/afe1g)