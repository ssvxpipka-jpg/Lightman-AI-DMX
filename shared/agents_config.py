"""
Lightman Agent Configuration
=============================
Configures all LangGraph agents to use the LOCAL LLM endpoint (Ollama).

NO paid API keys are used anywhere. All LLM inference is local.

Agents:
    1.  Main Agent          — orchestrates all other agents
    2.  Audio Agent         — processes audio features (beat, spectral flux)
    3.  Tracking Agent      — processes IP camera pose/object data
    4.  Light Agent         — generates lighting cues and DMX values
    5.  Assistant Agent     — chat interface for the Director user
    6.  Live Light Agent    — selects fixtures for live light priority
    7.  Researcher Agent    — searches RAG knowledge base
    8.  Rehearsal Analyst   — analyzes rehearsal recordings
    9.  Script Agent        — parses scripts into timelines
    10. Audience Profiler   — profiles audience for safety guidelines
"""

from __future__ import annotations

from typing import Any

from shared.config import get_logger

logger = get_logger("agents_config")

# ─── LLM Configuration ───────────────────────────────────────────────

# ONLY local LLM — no paid API keys anywhere
OLLAMA_URL = "http://localhost:11434"
OLLAMA_API_BASE = "http://localhost:11434/api"
OLLAMA_CHAT_ENDPOINT = "http://localhost:11434/api/chat"
OLLAMA_GENERATE_ENDPOINT = "http://localhost:11434/api/generate"

# Default models (local Ollama)
DEFAULT_MODEL = "llama3.2:latest"
LIGHTWEIGHT_MODEL = "phi3:latest"
CODING_MODEL = "qwen2.5-coder:latest"

# All agents must use the local LLM config
def get_llm_config(model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """
    Return LLM configuration pointing to local Ollama instance.
    No API keys required.
    """
    return {
        "model": model,
        "base_url": OLLAMA_URL,
        "api_base": OLLAMA_API_BASE,
        "provider": "ollama",
        "api_key": None,  # Explicitly None — no API keys
    }


# ─── Agent Registry ──────────────────────────────────────────────────

AGENT_CONFIGS: dict[str, dict[str, Any]] = {
    "main": {
        "name": "Main Agent",
        "description": "Orchestrates all other agents and manages overall lighting state.",
        "model": DEFAULT_MODEL,
        "llm_config": get_llm_config(),
    },
    "audio": {
        "name": "Audio Agent",
        "description": "Processes audio features (beat, spectral flux, volume) and sends OSC.",
        "model": LIGHTWEIGHT_MODEL,
        "llm_config": get_llm_config(LIGHTWEIGHT_MODEL),
    },
    "tracking": {
        "name": "Tracking Agent",
        "description": "Processes IP camera pose and object detection data.",
        "model": DEFAULT_MODEL,
        "llm_config": get_llm_config(),
    },
    "light": {
        "name": "Light Agent",
        "description": "Generates lighting cues, DMX values, and fixture priorities.",
        "model": CODING_MODEL,
        "llm_config": get_llm_config(CODING_MODEL),
    },
    "assistant": {
        "name": "Assistant Agent",
        "description": "Natural language chat interface for the Director user.",
        "model": DEFAULT_MODEL,
        "llm_config": get_llm_config(),
    },
    "live_light": {
        "name": "Live Light Agent",
        "description": "Selects fixtures by priority for live light based on movement and beat.",
        "model": LIGHTWEIGHT_MODEL,
        "llm_config": get_llm_config(LIGHTWEIGHT_MODEL),
    },
    "researcher": {
        "name": "Researcher Agent",
        "description": "Searches the RAG knowledge base and web content.",
        "model": DEFAULT_MODEL,
        "llm_config": get_llm_config(),
    },
    "rehearsal_analyst": {
        "name": "Rehearsal Analyst",
        "description": "Analyzes rehearsal recordings and generates reports.",
        "model": DEFAULT_MODEL,
        "llm_config": get_llm_config(),
    },
    "script": {
        "name": "Script Agent",
        "description": "Parses scripts into timelines with anchors.",
        "model": DEFAULT_MODEL,
        "llm_config": get_llm_config(),
    },
    "audience_profiler": {
        "name": "Audience Profiler",
        "description": "Profiles audience type for safety guidelines.",
        "model": LIGHTWEIGHT_MODEL,
        "llm_config": get_llm_config(LIGHTWEIGHT_MODEL),
    },
}


def get_all_agent_configs() -> list[dict[str, Any]]:
    """Return all agent configurations."""
    return list(AGENT_CONFIGS.values())


def get_agent_config(agent_key: str) -> dict[str, Any]:
    """Get configuration for a specific agent by key."""
    config = AGENT_CONFIGS.get(agent_key)
    if config is None:
        logger.warning("Unknown agent key: %s", agent_key)
        return get_llm_config()
    return config


def verify_no_api_keys() -> bool:
    """
    Verify that no paid API keys are configured.
    Returns True if all agents use local LLM only.
    """
    for key, cfg in AGENT_CONFIGS.items():
        if cfg["llm_config"].get("api_key") is not None:
            logger.error("Agent '%s' has an API key configured — VIOLATION!", key)
            return False
        if cfg["llm_config"].get("provider") != "ollama":
            logger.error("Agent '%s' uses non-local provider — VIOLATION!", key)
            return False
    logger.info("All agents configured for local LLM only — no API keys")
    return True
