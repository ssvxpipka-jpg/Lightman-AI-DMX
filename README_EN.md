# Lightman AI DMX

**AI assistant for console OS (Titan, grandMA3, EOS). Open-source, local-first.**

**AI assistant for console OS. Open-source, local-first stage lighting control.**

[↓ Download latest release](https://github.com/ssvxpipka-jpg/Lightman/releases/latest) | [❤️ Support the Project (DonationAlerts)](https://www.donationalerts.com/r/afe1g)

---

## About the project

Lightman is not a console replacement — it's an intelligence layer on top. It sees the 3D scene via bundled BlenderDMX, understands DMX protocols (Art-Net, sACN, OSC), and assists the operator. Runs locally, no telemetry.

---

## ✨ Features

- **AI Director (BYOK)**: Supports Groq, OpenRouter, Gemini, Mistral, Cerebras.
- **BlenderDMX 3D Studio**: Bundled Blender with BlenderDMX addon (Universal2 for macOS).
- **EpocCam Vision**: Computer vision via webcam (actor tracking, beam analysis, Haze density estimation).
- **Local RAG Knowledge Base**: 300+ fixtures and DMX protocols in ChromaDB, fully local.
- **Absolute Blackout**: Hard LOCK (AI cannot override, 2% work light).
- **Console OS Integration**: Connects to console OS (Titan, grandMA3, EOS) via IP.

---

## 🗺️ DMX Channel Configuration

Lightman uses fixture definition data from `fixtures_db/fixtures_catalog.json` to map DMX channels. Each fixture entry includes:

- `dmx_channels` — number of DMX channels (typically 2–12)
- `type` — fixture type (spot/wash/beam), determines default channel layout
- `modes` — modes of operation (e.g., `1ch`, `2ch`, `12ch`)

**How to set/channel configure:**

1. **Through fixture catalog**: Edit `fixtures_db/fixtures_catalog.json` — modify `dmx_channels` and `modes` for any fixture
2. **Through BlenderDMX addon**: The addon reads fixture data and auto-generates channel mappings
3. **OSC mapping** (optional): Lightman sends `/lightman/bpm`, `/lightman/beat`, `/lightman/energy` — these can map to console channels via custom OSC routing

### Typical DMX channel layout per fixture type:

| Fixture Type | Channels | Functions |
|---|---|---|
| **Spot/Beam** (e.g., Sharpy) | 2–4 | Red, Green, Blue, Gobo/Strobe |
| **Wash** (e.g., LED Wash) | 8–12 | RGB, Dimmer, Strobe, Zoom, Focus |
| **PAR** | 3–4 | Red, Green, Blue, Master Dimmer |

**Control methods:**

- **DMX universes** — via BlenderDMX addon + physical DMX interface
- **Art-Net/sACN** — network protocol for professional consoles (Titan, grandMA3)
- **OSC** — Lightman sends `/lightman/bpm`, `/lightman/beat`, `/lightman/energy` via UDP

### For integration with Titan/GrandMA:

Set OSC addresses in `shared/osc_bridge.py` to match your console format, or use a DMX gateway between Lightman and the console network.

The project is distributed under the **MIT License**. We follow the **Open Core** model:

- **v1.x – v3.x (Free Forever)**: The core system, AI Director, 3D editor, and base integrations are free for everyone.
- **v4.0+ (Paid Modules)**: Starting from v4, we plan to introduce advanced enterprise modules (extended AI backup for large venues, tracking, intercoms) via paid subscription. The core will remain open.

---

## 🚀 Installation

### Installation via GitHub Releases

The easiest way — download the ready build from releases. Nothing to install, just download and run!

### Installation guide:

1. **Go to releases**: Visit [GitHub Releases](https://github.com/ssvxpipka-jpg/Lightman/releases/latest)
2. **Download Installer:**
   - **Windows:** `Lightman-installer.exe` (automatic installation via wizard)
   - **macOS:** `Lightman-dmg.dmg` (archive for drag-and-drop into Applications)
3. **Install the program:**
   - **Windows:** Run the `.exe` file and follow the installation wizard:
     - Click "Next"
     - Click "I Agree"
     - Click "Install"
     - Done! Lightman will appear in the Start menu
   - **macOS:** 
     - Open the `.dmg` file
     - Drag the Lightman icon to the Applications folder
     - Right-click on the Applications icon → "Open" (first time to bypass Gatekeeper)
     - Lightman will appear in Launchpad
4. **Launch Lightman:**
   - **Windows:** Find the icon in the Start menu
   - **macOS:** Find in Launchpad
5. **Start working:** The program will automatically detect connected DMX equipment

### If the program doesn't run:

- **Windows:** Click "Run anyway" when warned by Windows
- **macOS:** System Settings → General → "Open anyway" next to Lightman

---

## 🏷️ Tags for search

`ai` `stage-lighting` `dmx` `lighting-control` `pyside6` `langgraph` `chromadb` `blenderdmx` `opencv` `macos` `windows` `linux` `open-source` `byok` `theatre-tech` `epoccam`

---

[❤️ Support the Project (DonationAlerts)](https://www.donationalerts.com/r/afe1g)
