# 🎭 Lightman — AI Stage Lighting Automation

**[🇷🇺 Русская версия](README.md) | [🇬🇧 English version]**

**Lightman** is a completely free, open-source ecosystem for AI-powered stage lighting automation. Forget manual beam focusing — the AI will track actors, sync with music, and understand your script.

## ✨ Key Features
*   🖥 **Director (The Brain)**: DaVinci Resolve-style dark UI, 3D stage with fixture placement, AI chat, cue timeline.
*   🧠 **Smart AI (BYOK)**: Connect to any cloud provider using your own API key (no subscriptions).
*   📚 **Local RAG**: Load your script and fixtures — the AI learns them *instantly* and for free right on your machine.
*   🎵 **Sound (The Ears)**: System audio capture (BlackHole), BPM/beat detection, OSC transmission.
*   💡 **Light (The Hands)**: Direct connection to console OS (Titan OS, grandMA3 OS, ChamSys OS, ETC Eos OS, QLC+ OS).

## 🚀 Installation (macOS)
Ready-to-use installers for Mac users are available!

1. Go to the **[Releases](https://github.com/ssvxpuk/lightman/releases)** page.
2. Download:
   * `Lightman.dmg` (Main app)
   * `LightmanSound.dmg` (Sound app)
   * `LightmanLight.dmg` (Lighting app)
3. Open the `.dmg` and drag the apps to your **Applications** folder.
4. *Note:* If macOS says "App is damaged", run this in Terminal: `xattr -cr /Applications/Lightman.app`.

### 🐧 Windows and Linux
No pre-built `.exe` or `.deb` yet, but you can build them from source:
*   **Windows**: Install Python 3.12, run `pip install -r requirements.txt`, and execute `scripts\build_win.bat`.
*   **Linux**: Run `bash scripts/build_linux.sh`.

## 🧠 How to setup AI (BYOK)
We don't charge for AI usage. You use your own key (Bring Your Own Key). It's fast and free.

1. Register with any free provider:
   * **[Groq](https://console.groq.com)** (Fastest, no credit card)
   * **[OpenRouter](https://openrouter.ai)** (Has free models)
   * **[ZvenoAI](https://zveno.ai)** (Works in Russia without VPN)
2. Copy your API key.
3. In the **Director** app, click **⚙ Settings** -> **AI Provider** tab.
4. Paste the key and click **Save**.
*A popup will confirm the AI has been trained on your fixtures.*

## 🛠 Tech Stack
*   **UI**: PySide6 + PyQtGraph (OpenGL)
*   **AI**: LangGraph + ChatOpenAI (BYOK)
*   **RAG**: ChromaDB (Local, no cloud)
*   **Audio**: Librosa + Sounddevice
*   **Network**: Python-OSC

## 🗺️ Roadmap
- [x] Beautiful UI and 3D scene
- [x] AI integration and local RAG training
- [x] Cross-platform apps (Director, Sound, Light)
- [ ] Lightman Server OS (v2.0)
- [ ] MIDI controllers support

## 📄 License
Distributed under the **MIT License**. Use it in schools, theaters, and weddings.

*Made with love for theater and hatred for manual beam focusing.* 🎭