# Lightman

**Stage lighting automation system for school theater**

Lightman is a comprehensive, AI-driven stage lighting control system designed for school theater productions. It connects audio input to lighting output, tracks actors via IP cameras, and orchestrates multi-agent AI coordination for intelligent light automation.

## Features

- **Three Applications**: Director (control center), Sound (audio capture), Light (fixture control)
- **BLE Pairing**: Secure code-based pairing between apps using HMAC-SHA256
- **Multi-Agent AI**: 9 specialized agents powered by LangGraph
- **IP Camera Tracking**: Human pose and object detection via MediaPipe
- **3D Scene Visualization**: PyQtGraph OpenGL scene with fixture library
- **RAG Knowledge Base**: ChromaDB + sentence-transformers, 5 languages, fully local
- **Multiple Console Support**: Titan, GrandMA3/2, ChamSys, ETC Eos, QLC+
- **Haze Analyzer**: AI reads the camera to check if there's enough smoke for beams to be visible. Tells you when to hit the hazer!
- **Rehearsal Recording**: Playback at 2x/3x/5x speed with AI analysis
- **Blackout Safety**: Automatic AI dimming when lights go to 0%

## Quick Start

```bash
# Install (requires Python 3.10+)
bash installers/install.sh      # macOS/Linux (auto-installs Ollama + Qwen model)
# or
python installers/install.py    # Cross-platform (Windows, auto-installs Ollama)

# Activate virtual environment
source venv/bin/activate        # macOS/Linux
venv\\Scripts\\activate          # Windows

# Run the Director
python -m src.director.main
```

### PySide6 Compatibility

On macOS 12 (Monterey) with Python 3.14, PySide6 6.10+ may fail to install.
The installer automatically falls back to PySide6 6.9.3 on macOS. For best
results, use Python 3.12 on macOS 12.

## Cross-Platform

Lightman runs on **macOS**, **Windows**, and **Linux** using `pathlib.Path` for all file operations. Logs are written to `~/.lightman/logs/lightman.log`.

## Project Structure

```
lightman/
├── src/
│   ├── director/     # Main control center application
│   ├── sound/        # Audio capture and OSC sending
│   └── light/        # DMX/console control application
├── shared/           # Shared modules (pairing, auth, agents, etc.)
├── data/             # Runtime data (users.db, profiles)
├── config/           # Configuration files (servers.yaml)
├── vendor/           # Cloned open-source libraries (read-only)
├── docs/             # Documentation
├── assets/           # Icons, models, images
├── installers/       # Installation scripts (install.sh, install.bat, install.py)
├── fixtures_db/      # GDTF fixture definitions
├── knowledge_base/   # RAG documents and embeddings
├── tests/            # Unit tests
├── deploy/           # Deployment guides
└── .lightman_secrets/ # Private data (codes, configs)
```

## Roadmap

### ALPHA (Current)
- BLE pairing between apps
- Basic authentication and user profiles
- Sound app with OSC output
- Light app with console plugins
- Director with 3D scene and studio tab
- Multi-agent system (9 agents)
- Basic IP camera tracking
- Blackout safety guard
- RAG knowledge base

### BETA
- Full console integration (Titan, GrandMA3/2, ChamSys, ETC Eos, QLC+)
- Haze/Smoke analyzer with IP camera feed monitoring
- Console auto-discovery and fixture patching
- Advanced pose tracking and actor light assignment
- Real 3D beam visualization with fixture data (beam angles from catalog)
- MIDI input/output support
- Microphone array spatial audio
- Ollama auto-install with qwen2.5-coder:3b model
- AI agent chat integration with haze warnings

### 1.0 (Production Release)
- Script agent with timeline comparison
- Rehearsal recording and playback
- Audience profiler with safety guidelines
- Full 3D fixture visualization
- Chat-based AI assistant

### 1.1 (Audio/MIDI Expansion)
- MIDI control surface support
- Live audio mixing via MIDI
- Music library integration
- Real-time spectrum visualization

### 2.0 (Server OS)
- Dedicated Lightman Server OS image
- Centralized control for multi-room theaters
- Hardware abstraction layer
- Network-wide device discovery and management

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

This project is developed for a school theater program. See the [Developer Roadmap](docs/development_roadmap.md) for contribution guidelines.
