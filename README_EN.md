# 🎭 Lightman

**[🇷🇺 Русская версия](README.md) | [🇬🇧 English version]**

> [!WARNING]
> **⚠️ ATTENTION: This is an early Beta version (v0.1.0)!**
> This project was built overnight (in 24 hours). Currently, there are **many stubs** in the code, the UI might be a bit rough, and some features (like AI chat) are not yet connected to the real neural network. We are actively working towards a stable **v1.0 release**. Thank you for your patience and testing!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)]()
[![AI](https://img.shields.io/badge/AI-Local%20%2F%20Ollama-green.svg)]()

**Lightman** is a completely free, open-source stage lighting automation system designed for school theaters, small studios, and beginner lighting operators.

Forget about manually following actors with beams. Forget about struggling to hit the beat. AI will handle the routine so you can focus on creativity.

---

## ✨ Key Features

*   🪄 **Turnkey Installation**: Forget the terminal. On the first launch, the app will automatically download and configure the local AI (Ollama). Just drag and drop to Applications.
*   🧠 **9 AI Agents**: Multi-agent system (LangGraph) that distributes tasks automatically.
*   📹 **Real-time Tracking**: Connect an old phone as an RTSP IP camera to track actors' poses and movements (YOLOv8).
*   🎵 **Music Sync**: BPM, beat, and spectrum analysis for dynamic lighting.
*   🎬 **Script Mode**: Load a `script.txt`, and the AI will know what's happening on stage.
*   🚨 **Blackout Rule (Sacred)**: AI will never turn on the lights if the operator hits Blackout.
*   🎛️ **Massive Fixture Database**: Catalog of 300+ real-world fixtures with real DMX channels and beam angles.
*   🌫️ **Haze Analyzer**: AI uses the camera to check if the light beams are visible and tells you when to hit the hazer.
*   💸 **Completely Free**: No API keys, no subscriptions.
*   🤫 **Secret Feature (Hidden in the smoke)**: *(Hidden from casual eyes...)* The built-in **Haze Analyzer** reads the camera feed and tells you when the beams are barely visible. Try looking into the settings. 🤫

---

## 🎛️ Three Operating Modes

1.  **🔴 Full Auto**: AI takes over **almost everything**. Controls colors, moves LED bars, and spins moving heads to the music.
2.  **🟡 Assist**: AI **adds live lighting**. Follows actors, backs you up. Adds subtle lighting accents on the beat.
3.  **🟢 Follow Only**: You have full control, AI only tracks the actor. **BUT!** If you miss the rhythm, AI takes over the **LED bars** for a split second to hit the beat.

---

## 🚀 Installation (In 3 minutes)

**Step 1: Download the Installer**
Download the `Lightman-Beta.dmg` file from the **Releases** section on GitHub.

**Step 2: Install**
Open the downloaded file and drag the **Lightman** icon into the **Applications** folder.

**Step 3: Run & Auto-Install**
Open Lightman. On the first launch, a window will appear: *"Ollama is not installed. Setting up automatically..."* The app will download Ollama and the required model. Wait for the progress bar to finish!

---

## 🗺️ Roadmap & Future Plans

**This project is built for the people.** If you like Lightman, if you star ⭐ the repo, and tell your friends, we will keep developing it and add:

*   🟢 **ALPHA / BETA (Current)**: Basic UI, BLE, Blackout rule, 3 modes, 3D scene, Haze Analyzer.
*   🟡 **Version 1.0**: Bug fixes, stability improvements, UI enhancements.
*   🟠 **Version 1.5 (Next Patch)**:
    *   **User Profiles**: All settings, fixtures, and backups are saved locally under your login.
    *   **Fixture Rating System**: Ability to "like" fixtures so the AI knows your preferences.
    *   **MIDI, DJ & Sound Consoles Support**: Control physical equipment.
*   🔴 **Version 2.0 (Lightman Server OS - All-in-One)**:
    *   **Two-way IP Authentication**: Secure connection with server whitelisting.
    *   **Hybrid Server**: Custom Linux-based OS with a GUI.
    *   **Fallback Mode**: If the main laptop crashes, control the show directly from the server.
    *   **Team Management**: Create workgroups (Teams) in the server admin panel. Assign roles (Lighting, Sound, Video Director).
*   🌌 **Version 5.0 (Distant Future - Ultimate Vision)**:
    *   **Full Broadcast & Sound Management System**: Unifying light, sound, and video into one ecosystem.
    *   **Smart AI Assistant**: A neural network that remembers EVERYTHING about your shows and does everything for you.
    *   **Script Analysis & Correction**: AI reads the script, analyzes it, and suggests corrections on the fly.
    *   **Song Selection**: Automatic track selection based on the scene's mood.
    *   **Intercom Integration**: Built-in voice chat with the entire team directly inside Lightman.

---

## ❤️ Support the Author
The project was built overnight at a crazy pace, without budgets or sponsors. If you liked the development and want to support the author:
[![DonationAlerts]https://www.donationalerts.com/r/afe1g

## 📄 License
Distributed under the **MIT License**. Use it in schools and theaters.