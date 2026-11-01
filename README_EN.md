# Lightman

**Fast, no-nonsense director tool for operators who don't want another 20kg console.**

Open-source stage lighting control for small venues and rental houses. Desktop, macOS (Apple Silicon), Python + PySide6. An AI assistant sees the 3D scene and can drive it. No server, no accounts, no telemetry — everything runs locally.

---

### What it is

Lightman is a desktop application for controlling stage lighting in small venues: school halls, theatres, rental houses. Instead of a heavy console — a laptop, a 3D viewport, and an AI assistant that sees the scene and understands what's going on.

Everything runs **locally**. No servers, no accounts, no cloud telemetry. Your scenes, scripts and knowledge base never leave the machine.

### Features

**Director — AI chat**

- Pick your LLM: Groq, OpenRouter, Gemini, Mistral, Cerebras, or any OpenAI-compatible endpoint (including local Ollama and LM Studio)
- The AI sees the current scene: fixtures, positions, intensities, dead zones
- Can spawn and remove fixtures through hidden `[SPAWN: …]` / `[REMOVE: …]` markers — the operator only sees the result, never the markers

**Three AI autonomy modes** (Settings → AI Mode; they shape both the prompt and the behaviour)

- 🟢 **Easy** — AI proposes, ✅ / ❌ buttons appear under the answer, the operator decides
- 🟡 **Medium** — AI applies routine actions itself, an **Undo** button lives for 10 seconds
- 🔴 **Hard** — AI applies instantly, no undo. Only Blackout can stop it

**Studio 3D**

- Real-time OpenGL viewport (pyqtgraph)
- Fixtures, trusses (truss / stand / box), dead zones
- Intensity 0–100 per fixture — currently drives mesh transparency, later goes into real DMX
- Click to select, eraser to delete
- Scene save/load to `data/scene.json`

**Blackout — absolute override**

- `Esc` or the ⬛ **Blackout** button → instant LOCK
- Freezes: chat, Settings, AI spawn/remove
- Work light drops to **2 %** — the stage never goes fully dark
- The AI **cannot** cancel, continue, or suggest continuing a Blackout
- ▶ **Resume** restores each fixture's pre-blackout intensity
- If even one fixture failed to hit 0 % — the LOCK **does not engage** and the operator gets a warning in Session Log

**Dead zones — a hard no-fly list**

- Lasers and bright beams are never aimed into a dead zone's bounding box
- The rule is baked into the AI system prompt and visible in 3D
- Lasers in dead zones are forbidden at the architecture level

**Auth and shell**

- Local login / sign-up (JSON, no server)
- Six tabs: Director · Studio 3D · Timeline · Script · Rehearsals · Profile
- Session Log at the bottom with a colour-coded event feed
- UI in English and Russian
- DaVinci-style dark theme, accent `#ff8a00`

**Local AI training (RAG)**

- Knowledge base built from show scripts and the fixture catalogue
- Embeddings via `DefaultEmbeddingFunction` — **no OpenAI key**
- Storage: `.lightman_cache/rag`
- Text never leaves the machine

### Installation

**From `.dmg` (Apple Silicon: M1 / M2 / M3 / M4)**

- macOS 12 Monterey or newer
- Ad-hoc signature → Gatekeeper complains on first launch. One command:

```bash
xattr -cr /Applications/Lightman.app
```

**From source**

```bash
python src/director/main.py
```

### Roadmap

**Now (v1.x — stabilisation)**
- Work light UI toggle, work light fixtures in the catalogue
- Tightening the `ui_3d.py` ↔ `studio_page.py` contract
- Loading the full fixture catalogue (300+ units, LED bars)

**Soon (v1.3+)**
- DMX record / playback
- BPM sync with the Sound app

**Later (v2.0+)**
- Fail-safe: on DMX loss the AI holds state and does not take over

**Further out (v4.0+)**
- CV for broadcasts (Laplacian variance already lives in `haze_analyzer`)
- Paid modules: extended AI backup for large venues, tracking, intercoms

### Tech stack

- Python 3.10+ (tested on 3.11)
- PySide6, pyqtgraph, OpenGL
- LangGraph + LangChain Core
- ChromaDB (local RAG)
- PyInstaller + dmgbuild (`.dmg` packaging)

### Repo layout

```
Lightman/
├── src/director/
│   ├── main.py               # shell, tabs, settings, blackout
│   ├── ui_3d.py              # OpenGL viewport
│   ├── theme.qss             # dark theme
│   └── studio_3d/            # 3D tab: panels, tools
├── shared/
│   ├── auth.py               # local login
│   ├── rag_init.py           # knowledge base
│   ├── agents_config.py      # LangGraph: director + specialists
│   └── i18n.py               # translations
├── fixtures_db/
│   └── fixtures_catalog.json
└── data/
    ├── script.txt            # optional, fed into RAG
    └── settings.json         # created on save (.gitignore'd)
```

### License

MIT. **Open Core**: the core stays free forever, paid tiers only add new modules in v4+.