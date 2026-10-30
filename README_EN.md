# 🎭 Lightman

**[🇷🇺 Русская версия](README.md) | [🇬🇧 English version]**

**Lightman** is a completely free, open-source stage lighting automation system designed for school theaters, small studios, and beginner lighting operators.

Forget about manually following actors with beams. AI will handle the routine so you can focus on creativity.

## ✨ Key Features
*   🧠 **9 AI Agents**: Multi-agent system (LangGraph).
*   📹 **Real-time Tracking**: Connect an old phone as an RTSP IP camera to track actors' poses.
*   🎵 **Music Sync**: BPM and beat analysis for dynamic lighting.
*   🌫️ **Haze Analyzer**: AI reads the camera to check if there's enough smoke for beams to be visible. Tells you when to hit the hazer!
*   🚨 **Blackout Rule**: AI will never turn on the lights if the operator hits Blackout.
*   💸 **Completely Free**: Runs on the local Ollama AI. No API keys.

## 🎛️ Three Operating Modes
1.  **🔴 Full Auto**: AI takes over almost everything. Controls colors, moves LED bars to the music.
2.  **🟡 Assist**: AI adds live lighting and backs you up if the beam drifts.
3.  **🟢 Follow Only**: You have full control, AI tracks the actor. If you miss the rhythm, AI takes over the LED bars for a split second to hit the beat.

## 🚀 Installation
1. Clone the repository: `git clone https://github.com/your-username/lightman.git`
2. Run the installer (auto-installs Ollama and qwen2.5-coder:3b): `bash installers/install.sh` (Mac/Linux) or `python installers/install.py` (cross-platform).
3. Activate: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
4. Run: `python -m src.director.main`

### PySide6 Compatibility
On macOS 12 (Monterey) with Python 3.14, the installer automatically falls back to `PySide6==6.9.3`.
For best results, use Python 3.12 on macOS 12.

## 🗺️ ROADMAP & FUTURE PLANS
**This project is built for the people.** If you like Lightman, if you star ⭐ the repo, and tell your friends, we will keep developing it and add:

*   🟢 **ALPHA / BETA (Current)**: Basic UI, BLE, Blackout rule, 3 modes, Haze Analyzer, Console Manager, 3D Beam Visualization, Ollama auto-install.
*   🟡 **Version 1.0**:
    *   **Bug Fixes**: Crash fixes, stability improvements.
    *   **Interface Updates**: UI redesign, adding new convenient controls.
    *   **Fun Patches**: Small quality-of-life features.
*   🟠 **Version 1.1 (If the community likes it)**:
    *   **MIDI Keyboards Support**: Control lights with physical faders.
    *   **DJ Consoles Support**: Sync with DJ equipment.
    *   **Sound Consoles Support**: "Sound Director" mode for audio engineers.
*   🔴 **Version 2.0 (Our Goal)**:
    *   **Lightman Server OS**: Custom Linux server OS.
    *   **Multi-user**: Connect up to 6 operators to one server to offload laptops.

## 📄 License
Distributed under the **MIT License**. Use it in schools and theaters.