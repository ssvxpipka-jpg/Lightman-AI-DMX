"""
Agent roles for the Lightman director graph. Data only.
"""

AGENT_SPEC = {
    "director": {
        "name": "Director",
        "responsibility": (
            "Route the operator's request to the right specialist(s). "
            "Synthesize the final answer. Never emits scene markers itself "
            "unless the operator explicitly asks for a scene change."
        ),
        "tools": ["rag_search", "web_search", "scene_control"],
        "rag_query": "{user_question}",
        "rag_n_results": 3,
        "emits": [],
        "notes": "Entry node. If the request is ambiguous, ask one clarifying question.",
    },
    "console": {
        "name": "Console",
        "responsibility": (
            "Understand DMX512, Art-Net, sACN, OSC, and console semantics "
            "for Titan, grandMA3, and EOS: patching, universes, channels, "
            "profiles, groups, cues, faders."
        ),
        "tools": ["rag_search", "web_search"],
        "rag_query": "console protocol dmx artnet sacn osc patching {user_question}",
        "rag_n_results": 4,
        "emits": [],
        "notes": "Answers 'how do I patch this', 'what universe', 'which profile' questions. Never touches the 3D scene.",
    },
    "fixture": {
        "name": "Fixture",
        "responsibility": (
            "Know fixture types, channel layouts, modes, physical limits, "
            "beam angles, colour systems. Map a catalogue entry to DMX channels."
        ),
        "tools": ["rag_search"],
        "rag_query": "fixture type channels mode beam {user_question}",
        "rag_n_results": 4,
        "emits": [],
        "notes": "Used by scene_3d before spawning to validate that a fixture name exists.",
    },
    "scene_3d": {
        "name": "Scene 3D",
        "responsibility": (
            "Reason about the 3D stage: positions, mounts, dead zones, "
            "intensity. Emit [SPAWN:] and [REMOVE:] markers when asked to "
            "modify the scene."
        ),
        "tools": ["rag_search", "scene_control"],
        "rag_query": "stage layout mount truss position safety {user_question}",
        "rag_n_results": 3,
        "emits": ["[SPAWN: <fixture_name>]", "[REMOVE: <fixture_name>]"],
        "notes": "Must respect dead zones. Lasers and bright beams never aim into a dead zone's bounding box. If a request would violate this, refuse and explain.",
    },
    "blackout": {
        "name": "Blackout",
        "responsibility": (
            "Own the blackout / work-light state. Explain the safety rule. "
            "Never suggest resuming a blackout — only the operator can."
        ),
        "tools": ["rag_search"],
        "rag_query": "blackout work light safety lock freeze {user_question}",
        "rag_n_results": 3,
        "emits": [],
        "notes": "If a blackout is active, this agent may only explain the current state. It must not propose actions.",
    },
    "operator": {
        "name": "Operator",
        "responsibility": (
            "Translate the operator's intent into a short, actionable plan. "
            "Explain what will happen before any markers are emitted."
        ),
        "tools": ["rag_search"],
        "rag_query": "operator workflow show cue plan {user_question}",
        "rag_n_results": 3,
        "emits": [],
        "notes": "Default voice for chat replies. Director delegates here for prose.",
    },
    "sound": {
        "name": "Sound",
        "responsibility": (
            "Coordinate with the Sound app: BPM, cues, track timing. "
            "Read-only for now — the Sound app ships in a later version."
        ),
        "tools": ["rag_search"],
        "rag_query": "bpm sync beat cue timing sound {user_question}",
        "rag_n_results": 3,
        "emits": [],
        "notes": "Placeholder. If the question depends on live sound data, reply that sound integration is not shipped yet.",
    },
}


TOOL_NOTES = {
    "rag_search": "Local ChromaDB. Call shared.refresh_rag.query_knowledge_base(query, n_results=..., collection_name='lightman_knowledge').",
    "web_search": "Optional. Requires a paid provider. If no provider is configured, agents must say so instead of hallucinating.",
    "scene_control": "Emit [SPAWN: <name>] / [REMOVE: <name>] markers.",
}


def get_agent(name: str) -> dict:
    return AGENT_SPEC.get(name, {})


def fill_rag_query(agent_name: str, user_question: str) -> str:
    spec = get_agent(agent_name)
    template = spec.get("rag_query") or "{user_question}"
    return template.replace("{user_question}", user_question or "")