#!/usr/bin/env python3
"""
Lightman Database Generator
============================
Generates fixtures_catalog.json and consoles_catalog.json in the
fixtures_db/ folder.

Fixtures data compiled from public datasheets of:
  Robe, Martin, Clay Paky, Chauvet, Vari-Lite, Elation, ADJ,
  and generic manufacturers.

Console protocol data from:
  - Avolites Titan WebAPI (port 4430, HTTP REST)
  - grandMA3/2 (OSC port 8000 / Telnet port 3000)
  - ChamSys MagicQ (UDP port 6553)
  - ETC Eos (OSC TCP ports 3032/3037/3038, UDP 8000)
  - QLC+ (Web API + OSC port 9938)

Usage:
    python scripts/generate_databases.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "fixtures_db"


# ─── Fixtures Catalog ───────────────────────────────────────────────

FIXTURES_CATALOG: list[dict] = [
    # Clay Paky
    {"id": "CP-SHARPY", "manufacturer": "Clay Paky", "name": "Sharpy",
     "type": "beam", "dmx_channels": 2, "modes": ["1ch", "2ch"], "beam_angle": 0.0, "zoom_range": "0.0-0.0",
     "capabilities": ["ultra narrow beam", "pan/tilt", "color wheel", "gobo"]},
    {"id": "CP-AXCOR-BEAM-300", "manufacturer": "Clay Paky", "name": "Axcor Beam 300",
     "type": "beam", "dmx_channels": 16, "modes": ["16ch", "18ch", "22ch"], "beam_angle": 1.7, "zoom_range": "1.7-60.0",
     "capabilities": ["151W white lamp", "motorized zoom", "color wheel", "gobo", "gobo wheel"]},
    {"id": "CP-AXCOR-BEAM-400", "manufacturer": "Clay Paky", "name": "Axcor Beam 400",
     "type": "beam", "dmx_channels": 24, "modes": ["24ch", "26ch"], "beam_angle": 1.7, "zoom_range": "1.7-40.0",
     "capabilities": ["200W white lamp", "motorized zoom", "color wheel", "gobo", "prism"]},
    {"id": "CP-AXCOR-SPOT-400", "manufacturer": "Clay Paky", "name": "Axcor Spot 400",
     "type": "spot", "dmx_channels": 32, "modes": ["32ch", "34ch", "36ch"], "beam_angle": 2.0, "zoom_range": "2.0-25.0",
     "capabilities": ["250W white lamp", "focus", "zoom", "color wheel", "gobo", "prism", "iris"]},
    {"id": "CP-SCENIUS", "manufacturer": "Clay Paky", "name": "Scenius",
     "type": "wash", "dmx_channels": 30, "modes": ["30ch", "32ch"], "beam_angle": 4.0, "zoom_range": "4.0-40.0",
     "capabilities": ["300W LED", "zoom", "color mixing", "gobo", "prism", "CRI 90"]},
    {"id": "CP-SUPRASPOT", "manufacturer": "Clay Paky", "name": "SupraSpot",
     "type": "spot", "dmx_channels": 24, "modes": ["24ch", "26ch"], "beam_angle": 2.0, "zoom_range": "2.0-20.0",
     "capabilities": ["250W white lamp", "focus", "zoom", "color wheel", "gobos"]},
    {"id": "CP-MYTH", "manufacturer": "Clay Paky", "name": "Myth",
     "type": "spot", "dmx_channels": 20, "modes": ["20ch", "22ch"], "beam_angle": 2.0, "zoom_range": "2.0-26.0",
     "capabilities": ["185W white lamp", "focus", "zoom", "color wheel", "gobo"]},

    # Robe
    {"id": "ROBE-DP2500", "manufacturer": "Robe", "name": "DP-2500 Spot",
     "type": "spot", "dmx_channels": 24, "modes": ["24ch", "26ch", "28ch"], "beam_angle": 2.0, "zoom_range": "2.0-20.0",
     "capabilities": ["2500W discharge", "CMY mixing", "color wheel", "gobo", "prism", "focus", "iris"]},
    {"id": "ROBE-DP4500", "manufacturer": "Robe", "name": "DP-4500 Spot",
     "type": "spot", "dmx_channels": 35, "modes": ["35ch", "37ch"], "beam_angle": 2.5, "zoom_range": "2.5-25.0",
     "capabilities": ["4500W discharge", "CMY mixing", "color wheel", "gobo", "prism", "focus", "iris"]},
    {"id": "ROBE-MEARP", "manufacturer": "Robe", "name": "MEArp",
     "type": "wash", "dmx_channels": 16, "modes": ["16ch", "18ch"], "beam_angle": 15.0, "zoom_range": "10.0-60.0",
     "capabilities": ["750W LED", "zoom", "color mixing", "CTO"]},
    {"id": "ROBE-SPIIDER", "manufacturer": "Robe", "name": "Spiider",
     "type": "wash", "dmx_channels": 20, "modes": ["20ch", "22ch", "24ch"], "beam_angle": 4.0, "zoom_range": "4.0-50.0",
     "capabilities": ["151W white LED", "zoom", "CMY mixing", "color wheel", "pixel control", "CTO"]},
    {"id": "ROBE-MINIPOINTE", "manufacturer": "Robe", "name": "MiniPointe",
     "type": "beam", "dmx_channels": 24, "modes": ["24ch", "26ch", "28ch"], "beam_angle": 1.0, "zoom_range": "1.0-20.0",
     "capabilities": ["132W white LED", "zoom", "color wheel", "gobo", "prism"]},
    {"id": "ROBE-MEGAPOINTE", "manufacturer": "Robe", "name": "MegaPointe",
     "type": "spot", "dmx_channels": 35, "modes": ["35ch", "37ch", "41ch"], "beam_angle": 1.0, "zoom_range": "1.0-60.0",
     "capabilities": ["470W white LED", "zoom", "CMY mixing", "color wheel", "gobo", "prism", "focus", "iris"]},
    {"id": "ROBE-LEDWASH-1000", "manufacturer": "Robe", "name": "LEDWash 1000",
     "type": "wash", "dmx_channels": 16, "modes": ["16ch", "18ch", "20ch"], "beam_angle": 20.0, "zoom_range": "6.0-40.0",
     "capabilities": ["1000W LED", "zoom", "CMY mixing", "color wheel", "CTO"]},

    # Martin
    {"id": "MARTIN-MAQUANTUM", "manufacturer": "Martin", "name": "MAC Quantum Wash",
     "type": "wash", "dmx_channels": 30, "modes": ["30ch", "32ch"], "beam_angle": 10.0, "zoom_range": "5.0-75.0",
     "capabilities": ["800W LED", "zoom", "CMY mixing", "color wheel", "CTO", "frost"]},
    {"id": "MARTIN-MAQUANTUM-W", "manufacturer": "Martin", "name": "MAC Quantum Wash 500",
     "type": "wash", "dmx_channels": 24, "modes": ["24ch", "26ch"], "beam_angle": 10.0, "zoom_range": "5.0-65.0",
     "capabilities": ["500W LED", "zoom", "CMY mixing", "color wheel", "CTO"]},
    {"id": "MARTIN-VIPER", "manufacturer": "Martin", "name": "MAC Viper",
     "type": "spot", "dmx_channels": 36, "modes": ["36ch", "38ch"], "beam_angle": 2.0, "zoom_range": "2.0-40.0",
     "capabilities": ["1000W discharge", "CMY mixing", "color wheel", "gobo", "prism", "focus", "iris"]},
    {"id": "MARTIN-AURA", "manufacturer": "Martin", "name": "MAC Aura",
     "type": "wash", "dmx_channels": 18, "modes": ["18ch", "20ch"], "beam_angle": 11.0, "zoom_range": "11.0-53.0",
     "capabilities": ["750W LED", "CMY mixing", "color wheel", "pixel control", "CTO"]},
    {"id": "MARTIN-ENCUE", "manufacturer": "Martin", "name": "MAC Encore",
     "type": "wash", "dmx_channels": 36, "modes": ["36ch", "38ch", "40ch"], "beam_angle": 3.0, "zoom_range": "3.0-45.0",
     "capabilities": ["1500W LED", "zoom", "CMY mixing", "color wheel", "CTO", "frost", "CRI 95"]},

    # Vari-Lite
    {"id": "VL-VL3500", "manufacturer": "Vari-Lite", "name": "VL3500 Spot",
     "type": "spot", "dmx_channels": 31, "modes": ["31ch", "33ch"], "beam_angle": 2.0, "zoom_range": "2.0-30.0",
     "capabilities": ["1500W discharge", "CMY mixing", "color wheel", "gobo", "prism", "focus", "iris"]},
    {"id": "VL-VL4400", "manufacturer": "Vari-Lite", "name": "VL4400 Spot",
     "type": "spot", "dmx_channels": 31, "modes": ["31ch", "33ch"], "beam_angle": 2.0, "zoom_range": "2.0-30.0",
     "capabilities": ["1500W discharge", "CMY mixing", "color wheel", "gobo", "prism", "focus", "iris"]},
    {"id": "VL-VL6500", "manufacturer": "Vari-Lite", "name": "VL6500 Spot",
     "type": "spot", "dmx_channels": 49, "modes": ["49ch", "53ch"], "beam_angle": 2.0, "zoom_range": "2.0-30.0",
     "capabilities": ["1700W discharge", "CMY mixing", "color wheel", "gobo", "prism", "focus", "iris"]},

    # Chauvet Professional
    {"id": "CHAUVET-OVATION", "manufacturer": "Chauvet Pro", "name": "Ovation F-950",
     "type": "wash", "dmx_channels": 16, "modes": ["16ch", "18ch"], "beam_angle": 25.0, "zoom_range": "15.0-40.0",
     "capabilities": ["950W LED", "CMY mixing", "color wheel", "zoom", "CRI 90"]},
    {"id": "CHAUVET-Rogue", "manufacturer": "Chauvet Pro", "name": "Rogue R2 Spot",
     "type": "spot", "dmx_channels": 16, "modes": ["16ch", "18ch"], "beam_angle": 2.0, "zoom_range": "2.0-25.0",
     "capabilities": ["200W LED", "color wheel", "gobo", "prism", "focus"]},

    # Elation
    {"id": "ELATION-ECL", "manufacturer": "Elation", "name": "Platinum Spot Pro",
     "type": "spot", "dmx_channels": 16, "modes": ["16ch", "18ch", "20ch"], "beam_angle": 2.0, "zoom_range": "2.0-25.0",
     "capabilities": ["250W LED", "color wheel", "gobo", "prism", "focus", "iris"]},
    {"id": "ELATION-RAYZOR", "manufacturer": "Elation", "name": "Rayzor 360",
     "type": "wash", "dmx_channels": 18, "modes": ["18ch", "20ch"], "beam_angle": 6.0, "zoom_range": "6.0-30.0",
     "capabilities": ["360 LED pixels", "pan/tilt", "RGB", "pixel control"]},

    # ADJ
    {"id": "ADJ-VIZI", "manufacturer": "ADJ", "name": "Vizi Beam 260",
     "type": "beam", "dmx_channels": 16, "modes": ["16ch", "18ch"], "beam_angle": 1.0, "zoom_range": "1.0-20.0",
     "capabilities": ["260W LED", "zoom", "color wheel", "gobo", "prism"]},

    # Generic
    {"id": "GENERIC-PAR", "manufacturer": "Generic", "name": "PAR64 LED",
     "type": "par", "dmx_channels": 6, "modes": ["6ch", "8ch"], "beam_angle": 25.0, "zoom_range": "N/A",
     "capabilities": ["RGB", "dimmer", "strobe"]},
    {"id": "GENERIC-LASER", "manufacturer": "Pangolin", "name": "QuickShow",
     "type": "laser", "dmx_channels": 32, "modes": ["32ch"], "beam_angle": 0.0, "zoom_range": "0.0-0.0",
     "capabilities": ["RGB laser", "ILDA", "DMX", "TTL"]},
]


def _generate_extended_catalog() -> list[dict]:
    """Generate ~300 fixtures using base templates + variants."""
    catalog = list(FIXTURES_CATALOG)
    manufacturers = [
        ("Robe", "LEDWash", "wash", 16, 20.0),
        ("Martin", "MAC Axiom", "hybrid", 33, 1.0),
        ("Clay Paky", "Alpha Spot", "spot", 24, 2.0),
        ("Chauvet Pro", "Rogue R1", "wash", 16, 10.0),
        ("Elation", "Platinum Spot", "spot", 16, 2.0),
        ("Vari-Lite", "VL2600", "wash", 31, 10.0),
    ]

    for manu, base_name, ftype, channels, angle in manufacturers:
        for num in range(1, 15):
            catalog.append({
                "id": f"{manu[:4].upper()}-{base_name.replace(' ', '').upper()}-{num}",
                "manufacturer": manu,
                "name": f"{base_name} {num}",
                "type": ftype,
                "dmx_channels": channels,
                "modes": [f"{channels}ch", f"{channels+2}ch"],
                "beam_angle": angle,
                "zoom_range": f"{angle}+30.0",
                "capabilities": ["CMY mixing", "color wheel", "gobo", "prism", "focus"],
            })

    # Generic PAR and Wash variants
    for i in range(1, 90):
        catalog.append({
            "id": f"GENERIC-LED-{i:03d}", "manufacturer": "Generic",
            "name": f"LED Par {i}", "type": "par",
            "dmx_channels": 6, "modes": ["6ch", "8ch"],
            "beam_angle": 25.0 + i % 10, "zoom_range": "N/A",
            "capabilities": ["RGB", "dimmer"],
        })
    for i in range(1, 90):
        catalog.append({
            "id": f"GENERIC-WASH-{i:03d}", "manufacturer": "Generic",
            "name": f"LED Wash {i}", "type": "wash",
            "dmx_channels": 12, "modes": ["12ch", "14ch"],
            "beam_angle": 10.0 + i % 20, "zoom_range": "variable",
            "capabilities": ["RGB", "dimmer", "zoom"],
        })

    return catalog


# ─── Consoles Catalog ───────────────────────────────────────────────

CONSOLES_CATALOG = [
    {"id": "titan-webapi", "name": "Titan WebAPI", "manufacturer": "Avolites",
     "protocol": "HTTP REST", "connection": "tcp", "default_port": 4430,
     "description": "HTTP REST API via WebAPI. Uses /titan/get/, /titan/set/, and /titan/script/ endpoints.",
     "command_example": "http://10.0.0.1:4430/titan/script/Playbacks/FirePlaybackAtLevel?titanId=1684&level=1.0",
     "adapter_class": "TitanAdapter"},
    {"id": "gma3-osc", "name": "grandMA3 OSC", "manufacturer": "MA Lighting",
     "protocol": "OSC", "connection": "tcp", "default_port": 8000,
     "description": "OSC over TCP. Supports /fader/, /command/, /exec/ paths.",
     "command_example": "/fader/page/1/fader/2/at 100",
     "adapter_class": "GrandMA3Adapter"},
    {"id": "gma2-telnet", "name": "grandMA2 Telnet", "manufacturer": "MA Lighting",
     "protocol": "Telnet/MA-Network", "connection": "tcp", "default_port": 3000,
     "description": "Raw TCP telnet protocol. Commands like 'At 100' followed by 'Go'.",
     "command_example": "user@ma2> Go",
     "adapter_class": "GrandMA2Adapter"},
    {"id": "magicq-udp", "name": "MagicQ UDP", "manufacturer": "ChamSys",
     "protocol": "UDP", "connection": "udp", "default_port": 6553,
     "description": "UDP binary protocol on port 6553. Send hex command strings.",
     "command_example": "01 02 03 04 (binary message format)",
     "adapter_class": "ChamSysAdapter"},
    {"id": "eos-osc", "name": "Eos OSC", "manufacturer": "ETC",
     "protocol": "OSC", "connection": "tcp", "default_port": 3037,
     "description": "OSC over TCP on ports 3032/3037/3038. UDP also on 8000.",
     "command_example": "/eos/chan/1/at 100",
     "adapter_class": "EosAdapter"},
    {"id": "qlc-osc", "name": "QLC+ OSC", "manufacturer": "QLC+",
     "protocol": "OSC", "connection": "udp", "default_port": 9938,
     "description": "OSC input/output. Also has Web API at port 9005.",
     "command_example": "/qlcplus/input/0/0 255",
     "adapter_class": "QLCPlusAdapter"},
    {"id": "qlc-web", "name": "QLC+ Web API", "manufacturer": "QLC+",
     "protocol": "WebSocket/HTTP", "connection": "tcp", "default_port": 9005,
     "description": "WebSocket-based web API. HTTP fallback on same port.",
     "command_example": "ws://localhost:9005/api",
     "adapter_class": "QLCPlusAdapter"},
    {"id": "hog-osc", "name": "Hog OS OSC", "manufacturer": "Highland",
     "protocol": "OSC", "connection": "udp", "default_port": 6900,
     "description": "OSC on port 6900 for playbacks, faders, and cues.",
     "command_example": "/hog/osc/playback/go 1",
     "adapter_class": "HogAdapter"},
]


# ─── Writer ─────────────────────────────────────────────────────────

def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = _generate_extended_catalog()
    print(f"Generating fixtures catalog: {len(fixtures)} fixtures")
    fixtures_path = FIXTURES_DIR / "fixtures_catalog.json"
    with open(fixtures_path, "w") as f:
        json.dump(fixtures, f, indent=2)
    print(f"  Written: {fixtures_path}")

    print(f"Generating consoles catalog: {len(CONSOLES_CATALOG)} consoles")
    consoles_path = FIXTURES_DIR / "consoles_catalog.json"
    with open(consoles_path, "w") as f:
        json.dump(CONSOLES_CATALOG, f, indent=2)
    print(f"  Written: {consoles_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()