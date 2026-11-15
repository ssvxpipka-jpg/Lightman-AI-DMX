# Lightman AI DMX

**AI-ассистент для ОС пульта (Titan, grandMA3, EOS). Open-source, local-first.**

**AI assistant for console OS. Open-source, local-first stage lighting control.**

[↓ Скачать последний релиз](https://github.com/ssvxpipka-jpg/Lightman/releases/latest) | [❤️ Поддержать проект (DonationAlerts)](https://www.donationalerts.com/r/afe1g)

---

## О проекте

Lightman — это не замена консоли, а интеллектуальный слой поверх неё. Он видит 3D-сцену через встроенный BlenderDMX, понимает DMX-протоколы (Art-Net, sACN, OSC) и помогает световику, работая локально без телеметрии.

---

## ✨ Фичи

- **AI Director (BYOK)**: Подключение Groq, OpenRouter, Gemini, Mistral, - **AI Director (BYOK)**: Подключение Groный Blender с аддоном BlenderDMX (Universal2 для macOS).
- **EpocCam Vision**: Компьютерное зрение через веб-камеру (трекинг актеров, анализ лучей, оценка плотности дыма/Haze).
- **Local RAG Knowledge Base**: База знаний на 300+ приборов и DMX-протоколы (ChromaDB), работает полностью локально.
- **Absolute Blackout**: Жесткий LOCK (ИИ не может отменить, дежурный свет 2%).
- **Console OS Integration**: Подключение к ОС пультов (Titan, grandMA3, EOS) по IP.

---

## 🗺️ Настройка DMX каналов

Lightman использует файлы определения из `fixtures_db/fixtures_catalog.json` для маппинга DMX каналов. Каждая запись фиксации включает:

- `dmx_channels` — количество DMX каналов (обычно 2–12 шт)
- `type` — тип прибора (spot/wash/beam), определяет default channel layout
- `modes` — режимы работы (например, `1ch`, `2ch`, `12ch`)

**Как настроить каналы:**

1. **Через фиталог**: Редактируйте `fixtures_db/fixtures_catalog.json` — изменяйте `dmx_channels` и `modes` для любого прибора
2. **Через BlenderDMX addon**: Addon читает данные фиктов и автоматически генерирует маппинг каналов
3. **OSC маппинг** (опционально): Lightman шлет `/lightman/bpm`, `/lightman/beat`, `/lightman/energy` — эти можно мапить на каналы консоли через кастомную маршрутизацию OSC

### Типичная расстановка DMX каналов по типу прибора:

| Тип прибора | Каналы | Функции |
|:---:|:---:|:---|
| **Spot/Beam** (например, Sharpy) | 2–4 | Red, Green, Blue, Gobo/Strobe |
| **Wash** (например, LED Wash) | 8–12 | RGB, Dimmer, Strobe, Zoom, Focus |
| **PAR** | 3–4 | Red, Green, Blue, Master Dimmer |

**Способы контроля:**

- **DMX universes** — через BlenderDMX addon + физический DMX интерфейс
- **Art-Net/sACN** — сетевой протокол для профессиональных консолей (Titan, grandMA3)
- **OSC** — Lightman шлет `/lightman/bpm`, `/lightman/beat`, `/lightman/energy` по UDP

### Для интеграции с Titan/GrandMA:

Настройте адреса OSC в `shared/osc_bridge.py` под формат вашей консоли, либо используйте DMX шлюз между Lightman и сетью консоли.

Проект распространяется по лицензии **MIT**. Мы используем модель **Open Core**:

- **v1.x – v3.x (Бесплаво навсегда)**: Ядро системы, AI-директор, 3D-редактор и базовые интеграции доступны всем бесплатно без ограничений.
- **v4.0+ (Платные модули)**: Начиная с 4-й версии, мы планируем добавлять сложные корпоративные модули (расширенный AI-резерв для больших площадок, трекинг, интеркомы) по платной подписке. Базовое ядро останется открытым.

---

## 🚀 Установка через GitHub Releases

Самый простой способ — скачать готовую сборку из релизов. Ничего устанавливать не нужно, просто скачай и запусти!

### Инструкция по установке:

1. **Перейди в релисы**: Посети [GitHub Releases](https://github.com/ssvxpipka-jpg/Lightman/releases/latest)
2. **Скачай Installer:**
   - **Windows:** `Lightman-installer.exe` (автоматическая установка через мастера)
   - **macOS:** `Lightman-dmg.dmg` (архив для перетаскивания в Applications)
3. **Установи программу:**
   - **Windows:** Запусти `.exe` файл и следуй мастеру установки:
     - Нажми "Next"
     - Нажми "I Agree"
     - Нажми "Install"
     - Готово! Lightman появится в меню Пуск
   - **macOS:** 
     - Открой `.dmg` файл
     - Перетащи иконку Lightman в папку Applications
     - 右 клик на иконке в Applications → "Открыть" (первый раз для обхода Gatekeeper)
     - Lightman появится в Launchpad
4. **Запусти Lightman:**
   - **Windows:** Найди иконку в меню Пуск
   - **macOS:** Найди в Launchpad
5. **Начни работу:** Программа сама найдет подключенное DMX-оборудование

### Если программа не запускается:

- **Windows:** Нажми "Все равно запустить" при предупреждении от Windows
- **macOS:** Системные настройки → Общие → "Открыть все vezо" рядом с Lightman

---

## 🏷️ Теги для поиска

`ai` `stage-lighting` `dmx` `lighting-control` `pyside6` `langgraph` `chromadb` `blenderdmx` `opencv` `macos` `windows` `linux` `open-source` `byok` `theatre-tech` `epoccam`

---

[❤️ Поддержать проект (DonationAlerts)](https://www.donationalerts.com/r/afe1g)
