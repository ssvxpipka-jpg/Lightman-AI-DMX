# Lightman AI DMX

**AI assistant for console OS (Titan, grandMA3, EOS). Open-source, local-first.**

[**❤️ Support the Project (DonationAlerts)**](https://www.donationalerts.com/r/afe1g)

Lightman is not a console replacement — it's an intelligence layer on top. It sees the 3D scene via bundled BlenderDMX, understands DMX protocols (Art-Net, sACN, OSC), and assists the operator. Runs locally, no telemetry.

---

### 🚀 HOW TO INSTALL (SIMPLE GUIDE)

**⚠️ IMPORTANT: VS Code IS NOT NEEDED.**
To build the app, you only need a **Terminal** (command line), Python, and Git.

**Step 1. Setup (All OS)**
1. Download and install [Python 3.10+](https://www.python.org/downloads/). *(On Windows, check "Add Python to PATH" during installation)*.
2. Download and install [Git](https://git-scm.com/).
3. Open your terminal:
   * **On macOS / Linux:** press `Cmd + Space` (or `Ctrl + Alt + T`) and search for **Terminal**.
   * **On Windows:** press `Win + R`, type `powershell`, and press Enter.

**Step 2. Clone the project (All OS)**
In the terminal, copy and paste these two commands (one by one, pressing Enter):
```bash
git clone https://github.com/ssvxpipka-jpg/Lightman-AI-DMX.git
cd Lightman-AI-DMX
```

**Step 3. Install dependencies and build**

**🍏 For macOS (with automatic Blender & BlenderDMX setup)**
1. Install dependencies:
```bash
pip install -r requirements.txt pyinstaller
```
2. Download and bundle **Blender** and the **BlenderDMX** addon into the app (required for the 3D editor):
```bash
python3 scripts/bundle_blender.py
```
3. Build all apps:
```bash
pyinstaller Lightman.spec
pyinstaller --windowed --name LightmanSound src/sound/main.py
pyinstaller --windowed --name LightmanLight src/light/main.py
```
*(If blocked by Gatekeeper, run: `xattr -cr dist/Lightman.app`)*

**🪟 For Windows (manual Blender setup required for 3D)**
*(Note: The auto-bundling script is for macOS only. On Windows, you need to install Blender and BlenderDMX separately, or use the built-in fallback 3D view).*
```bash
pip install -r requirements.txt pyinstaller
pyinstaller Lightman.spec
pyinstaller --windowed --name LightmanSound src/sound/main.py
pyinstaller --windowed --name LightmanLight src/light/main.py
```

**🐧 For Linux (manual Blender setup required for 3D)**
```bash
sudo apt-get update && sudo apt-get install -y libegl1 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0
pip install -r requirements.txt pyinstaller
pyinstaller Lightman.spec
pyinstaller --windowed --name LightmanSound src/sound/main.py
pyinstaller --windowed --name LightmanLight src/light/main.py
```

**Step 4. Run**
Your built apps will be in the `dist/` folder inside the project directory (`.app` on Mac, `.exe` on Windows, binaries on Linux).

---

### ✨ Features
- **AI Director (BYOK)**: Supports Groq, OpenRouter, Gemini, Mistral, Cerebras.
- **BlenderDMX 3D Studio**: Bundled Blender with BlenderDMX addon (Universal2 for macOS).
- **EpocCam Vision**: Computer vision via webcam (actor tracking, beam analysis, Haze density estimation).
- **Local RAG Knowledge Base**: 300+ fixtures and DMX protocols in ChromaDB, fully local.
- **Absolute Blackout**: Hard LOCK (AI cannot override, 2% work light).
- **Console OS Integration**: Connects to console OS (Titan, grandMA3, EOS) via IP.

### 🗺️ Roadmap
- **v1.1.1 (Current Release)**: BlenderDMX integration, EpocCam Vision, UI logs, purple theme.
- **v1.1.2**: Full 300+ fixture library UI, smoke machines.
- **v1.2.0**: Multi-agent system (Sound, Light, Blackout agents), auto-calibration.
- **v2.0.0**: Dedicated OS server for Llama (local AI), tracking via admin panel, USB console support.

### 🛡️ License & Open Core Model
The project is distributed under the **MIT License**. We follow the **Open Core** model:
- **v1.x – v3.x (Free Forever)**: The core system, AI Director, 3D editor, and base integrations are free for everyone.
- **v4.0+ (Paid Modules)**: Starting from v4, we plan to introduce advanced enterprise modules (extended AI backup for large venues, tracking, intercoms) via paid subscription. The core will remain open.

### 🏷️ Topics
`ai` `stage-lighting` `dmx` `lighting-control` `pyside6` `langgraph` `chromadb` `blenderdmx` `opencv` `macos` `windows` `linux` `open-source` `byok` `theatre-tech` `epoccam`

---
[**❤️ Support the Project (DonationAlerts)**](https://www.donationalerts.com/r/afe1g)