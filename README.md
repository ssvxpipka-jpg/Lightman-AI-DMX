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

### 🛡️ Лицензия и Модель Open Core
Проект распространяется по лицензии **MIT**. Мы используем модель **Open Core**:
- **v1.x – v3.x (Бесплатно навсегда)**: Ядро системы, AI-директор, 3D-редактор и базовые интеграции доступны всем бесплатно без ограничений.
- **v4.0+ (Платные модули)**: Начиная с 4-й версии, мы планируем добавлять сложные корпоративные модули (расширенный AI-резерв для больших площадок, трекинг, интеркомы) по платной подписке. Базовое ядро останется открытым.

### 🗺️ Roadmap (Планы)
- **v1.1.1 (Текущий релиз)**: Интеграция BlenderDMX, EpocCam Vision, логи в UI, фиолетовая тема. *(Известный баг: старая вкладка 3D осталась в UI, будет убрана в v1.1.2).*
- **v1.1.2**: Удаление старой вкладки 3D, добавление полной библиотеки из 300+ приборов в UI (Drag & Drop), дым-машины.
- **v1.2.0**: Multi-agent система (ИИ-агенты для звука, света, блэкаута), авто-калибровка лучей.
- **v2.0.0**: Серверная ОС для Llama (локальный ИИ на отдельном железе), трекинг через админ-панель, поддержка USB-пультов.

### 🚀 Установка
1. Скачай установщик для своей ОС из [Releases](https://github.com/ssvxpipka-jpg/Lightman-AI-DMX/releases).
2. **macOS**: Открой `.dmg`, перетащи в Applications. Для первого запуска выполни в терминале: `xattr -cr /Applications/Lightman.app` (снимает блокировку Gatekeeper).
3. **Windows/Linux**: Запусти `.exe` или бинарник из архива.

### 🏷️ Topics (Теги для поиска)
`ai` `stage-lighting` `dmx` `lighting-control` `pyside6` `langgraph` `chromadb` `blenderdmx` `opencv` `macos` `windows` `linux` `open-source` `byok` `theatre-tech` `epoccam`

---
[**❤️ Поддержать проект (DonationAlerts)**](https://www.donationalerts.com/r/afe1g)