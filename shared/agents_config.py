"""
LangGraph agents — BYOK cloud architecture.

The local llama-cpp-python engine has been removed. All inference is done
through OpenAI-compatible endpoints (`ChatOpenAI`). The active provider,
API key, base URL and model are supplied at runtime via a `settings` dict.

Public API:
    PROVIDER_PRESETS     — dict of well-known providers
    get_llm(settings)    — returns a cached ChatOpenAI (singleton)
    reset_llm()          — clears the cached instance (e.g. after changing key)
    build_graph()        — compiles the LangGraph state machine
"""

import math
import logging
import re
from typing import TypedDict, List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from shared.rag_init import search_knowledge_base

logger = logging.getLogger(__name__)

VALID_ROUTES = {"audio", "tracking", "light", "live_light", "researcher", "assistant"}


# --------------------------------------------------------------- Providers
PROVIDER_PRESETS: Dict[str, Dict[str, str]] = {
    "Groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    "OpenRouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "deepseek/deepseek-chat:free",
    },
    "Google Gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.5-flash",
    },
    "Mistral AI": {
        "base_url": "https://api.mistral.ai/v1",
        "model": "mistral-small-latest",
    },
    "Cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "model": "llama-4-scout-17b-16e-instruct",
    },
    "ZvenoAI (RU)": {
        "base_url": "https://api.zveno.ai/v1",
        "model": "cohere/north-mini-code",
    },
    "Cloudflare Workers": {
        "base_url": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        "model": "@cf/meta/llama-3.1-8b-instruct",
    },
    "NVIDIA NIM": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.3-70b-instruct",
    },
    "Cohere": {
        "base_url": "https://api.cohere.com/v2",
        "model": "command-r-plus",
    },
    "SambaNova": {
        "base_url": "https://api.sambanova.ai/v1",
        "model": "Meta-Llama-3.3-70B-Instruct",
    },
    "Together AI": {
        "base_url": "https://api.together.xyz/v1",
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    },
    "DeepInfra": {
        "base_url": "https://api.deepinfra.com/v1/openai",
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    },
    "Hyperbolic": {
        "base_url": "https://api.hyperbolic.xyz/v1",
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    },
    "Novita AI": {
        "base_url": "https://api.novita.ai/v3/openai",
        "model": "meta-llama/llama-3.3-70b-instruct",
    },
    "Fireworks AI": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    },
    "Anyscale": {
        "base_url": "https://api.endpoints.anyscale.com/v1",
        "model": "meta-llama/Llama-3-70b-chat-hf",
    },
    "Lepton AI": {
        "base_url": "https://api.lepton.ai/api/v1",
        "model": "llama3-70b",
    },
    "Local Ollama (Server)": {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5-coder:3b",
    },
    "Local LM Studio": {
        "base_url": "http://localhost:1234/v1",
        "model": "local-model",
    },
    "Custom": {
        "base_url": "",
        "model": "",
    },
}


# --------------------------------------------------------------- Prompts
DIRECTOR_PROMPT = (
    "You are the Director agent for Lightman. Given the scene spatial data "
    "(cameras, hazers, stage bounds, no-laser zones, tracking camera, "
    "operator notes) and the user request, reply with EXACTLY one word: "
    "audio, tracking, light, live_light, researcher, or assistant."
)

AUDIO_PROMPT = (
    "You are the Audio agent for Lightman. Handle audio analysis, beat "
    "detection, BPM estimation, and audio-reactive lighting."
)

TRACKING_PROMPT = (
    "You are the Tracking agent for Lightman. Handle performer tracking, "
    "camera positions, follow-spot logic, and positional data."
)

LIGHT_PROMPT = (
    "You are the Light agent for Lightman. Handle fixture selection, DMX, "
    "colors, gobos, and static lighting. YOU MUST REFUSE any laser path that "
    "intersects a camera or enters a no-laser zone, and explain why."
)

LIVE_LIGHT_PROMPT = (
    "You are the Live Light agent for Lightman. Handle live cues, chases, "
    "and real-time operator commands. Never authorize a laser path that "
    "violates camera safety or no-laser zones."
)

RESEARCHER_PROMPT = (
    "You are the Researcher agent for Lightman. Look up fixture specs, DMX "
    "profiles, and manufacturer docs. Cite precisely."
)

ASSISTANT_PROMPT = (
    "You are the Assistant agent for Lightman. Help with general questions, "
    "configuration, and workflow guidance."
)

PROMPTS: Dict[str, str] = {
    "director": DIRECTOR_PROMPT,
    "audio": AUDIO_PROMPT,
    "tracking": TRACKING_PROMPT,
    "light": LIGHT_PROMPT,
    "live_light": LIVE_LIGHT_PROMPT,
    "researcher": RESEARCHER_PROMPT,
    "assistant": ASSISTANT_PROMPT,
}


# --------------------------------------------------------------- LLM cache
_LLM_INSTANCE: Optional[ChatOpenAI] = None
_LLM_CACHE_KEY: Optional[tuple] = None


def reset_llm() -> None:
    """Clear cached LLM so the next call rebuilds it (use after key change)."""
    global _LLM_INSTANCE, _LLM_CACHE_KEY
    _LLM_INSTANCE = None
    _LLM_CACHE_KEY = None


def _resolve_provider(settings: Dict[str, Any]) -> Dict[str, str]:
    """Return {'base_url': ..., 'model': ...} based on settings."""
    settings = settings or {}
    provider = settings.get("ai_provider") or "Groq"

    preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["Custom"]).copy()

    # Custom overrides
    custom_url = (settings.get("ai_base_url") or "").strip()
    custom_model = (settings.get("ai_model") or "").strip()

    if provider == "Custom" or custom_url:
        preset["base_url"] = custom_url or preset.get("base_url", "")
    if provider == "Custom" or custom_model:
        preset["model"] = custom_model or preset.get("model", "")

    return preset


def get_llm(settings: Dict[str, Any], system_prompt: str = "") -> ChatOpenAI:
    """
    Return a cached ChatOpenAI instance.

    Caching key = (provider, base_url, model, api_key, system_prompt).
    Changing any of these (e.g. user pastes a new key) rebuilds the instance.
    """
    global _LLM_INSTANCE, _LLM_CACHE_KEY

    settings = settings or {}
    provider = settings.get("ai_provider") or "Groq"
    api_key = (settings.get("ai_api_key") or "").strip()
    resolved = _resolve_provider(settings)
    base_url = resolved.get("base_url", "") or ""
    model = resolved.get("model", "") or ""

    cache_key = (provider, base_url, model, api_key, system_prompt)

    if _LLM_INSTANCE is not None and _LLM_CACHE_KEY == cache_key:
        return _LLM_INSTANCE

    if not base_url:
        raise ValueError(
            f"Provider '{provider}' has no base URL. "
            "Set it in Settings → AI Provider."
        )
    if not model:
        raise ValueError(
            f"Provider '{provider}' has no model name. "
            "Set it in Settings → AI Provider."
        )
    if not api_key:
        # Local servers (Ollama / LM Studio / Custom) may accept a dummy key.
        api_key = "not-needed"

    logger.info(
        "Initialising ChatOpenAI (provider=%s, model=%s, base_url=%s)",
        provider, model, base_url,
    )
    _LLM_INSTANCE = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.2,
        max_tokens=512,
        timeout=60,
        max_retries=0,  # we handle retries manually below
    )
    _LLM_CACHE_KEY = cache_key
    return _LLM_INSTANCE


def _invoke_with_retry(llm: ChatOpenAI, messages: List[Dict[str, str]],
                       retries: int = 2) -> str:
    """Call llm.invoke() with RateLimitError-aware retries."""
    import time
    try:
        from openai import RateLimitError  # type: ignore
    except Exception:
        RateLimitError = None  # type: ignore

    attempt = 0
    last_err: Optional[Exception] = None
    while attempt <= retries:
        try:
            result = llm.invoke(messages)
            return getattr(result, "content", str(result))
        except Exception as e:
            last_err = e
            is_rate = RateLimitError is not None and isinstance(e, RateLimitError)
            if not is_rate:
                raise
            delay = min(30, 2 ** attempt)
            logger.warning(
                "Rate limit hit (%s). Retrying in %ss (attempt %d/%d).",
                e, delay, attempt + 1, retries + 1,
            )
            time.sleep(delay)
            attempt += 1
    raise last_err if last_err else RuntimeError("Unknown LLM error")


# --------------------------------------------------------------- State
class AgentState(TypedDict, total=False):
    user_input: str
    route: str
    response: str
    history: List[Dict[str, str]]
    spatial: Dict[str, Any]
    settings: Dict[str, Any]


# --------------------------------------------------------------- Geometry
def _v(p) -> tuple:
    try:
        return (float(p[0]), float(p[1]), float(p[2]))
    except Exception:
        return (0.0, 0.0, 0.0)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(v):
    n = math.sqrt(_dot(v, v))
    return (0.0, 0.0, 0.0) if n == 0 else (v[0] / n, v[1] / n, v[2] / n)


def ray_intersects_aabb(origin, direction, b) -> bool:
    direction = _norm(_v(direction))
    origin = _v(origin)
    tmin, tmax = -float("inf"), float("inf")
    for axis, (lo_k, hi_k) in enumerate(
        [("min_x", "max_x"), ("min_y", "max_y"), ("min_z", "max_z")]
    ):
        lo = b.get(lo_k, -float("inf"))
        hi = b.get(hi_k, float("inf"))
        o = origin[axis]
        d = direction[axis]
        if abs(d) < 1e-9:
            if o < lo or o > hi:
                return False
        else:
            t1 = (lo - o) / d
            t2 = (hi - o) / d
            if t1 > t2:
                t1, t2 = t2, t1
            tmin = max(tmin, t1)
            tmax = min(tmax, t2)
            if tmin > tmax:
                return False
    return tmax >= 0


def ray_hits_sphere(origin, direction, center, radius=0.5) -> bool:
    o = _v(origin)
    d = _norm(_v(direction))
    c = _v(center)
    oc = _sub(c, o)
    t = _dot(oc, d)
    if t < 0:
        return False
    closest = (o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t)
    return sum((closest[i] - c[i]) ** 2 for i in range(3)) <= radius ** 2


def laser_path_issues(origin, direction, spatial: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    for cam in spatial.get("cameras", []) or []:
        if cam.get("position") and ray_hits_sphere(origin, direction, cam["position"]):
            issues.append(f"laser intersects camera '{cam.get('name', '?')}'")
    for z in spatial.get("no_laser_zones", []) or []:
        if ray_intersects_aabb(origin, direction, z):
            issues.append(f"laser enters no-laser zone '{z.get('name', '?')}'")
    return issues


# --------------------------------------------------------------- Context
def spatial_context_text(spatial: Optional[Dict[str, Any]]) -> str:
    if not spatial:
        return "No spatial data."
    lines: List[str] = []
    for cam in spatial.get("cameras", []) or []:
        lines.append(f"- Camera '{cam.get('name', '?')}' at {cam.get('position')}")
    for hz in spatial.get("hazers", []) or []:
        lines.append(
            f"- Hazer '{hz.get('name', '?')}' ({hz.get('side', '?')}) "
            f"at {hz.get('position')}"
        )
    sb = spatial.get("stage_bounds")
    if sb:
        lines.append(f"- Stage bounds: {sb}")
    for z in spatial.get("no_laser_zones", []) or []:
        lines.append(
            f"- No-laser zone '{z.get('name', '?')}': "
            f"x[{z.get('min_x')},{z.get('max_x')}] "
            f"y[{z.get('min_y')},{z.get('max_y')}] "
            f"z[{z.get('min_z')},{z.get('max_z')}]"
        )
    tcp = spatial.get("tracking_camera_pos")
    if tcp:
        lines.append(f"- Tracking camera position: {tcp}")
    cn = spatial.get("camera_notes")
    if cn:
        lines.append(f"- Operator camera notes: {cn}")
    return "\n".join(lines) if lines else "No objects defined in scene."


# --------------------------------------------------------------- Nodes
def _director_node():
    def node(state: AgentState) -> Dict[str, Any]:
        text = state.get("user_input", "") or ""
        sp = state.get("spatial") or {}
        settings = state.get("settings") or {}
        prompt = (
            "Classify this lighting request. Reply with EXACTLY one word from: "
            "audio, tracking, light, live_light, researcher, assistant.\n\n"
            f"Scene:\n{spatial_context_text(sp)}\n\nRequest: {text}"
        )
        route = "assistant"
        try:
            llm = get_llm(settings, DIRECTOR_PROMPT)
            r = _invoke_with_retry(
                llm, [{"role": "user", "content": prompt}]
            )
            words = (r or "").strip().lower().split()
            if words:
                w = words[0].strip(".,:;!?\"'`")
                if w in VALID_ROUTES:
                    route = w
        except Exception as e:
            logger.error("Director failed: %s", e)
        return {"route": route}

    return node


def _specialist_node(name: str):
    def node(state: AgentState) -> Dict[str, Any]:
        history = state.get("history") or []
        sp = state.get("spatial") or {}
        settings = state.get("settings") or {}
        user_input = state.get("user_input", "") or ""

        safety_note = ""
        if "laser" in user_input.lower():
            origin = sp.get("laser_origin")
            direction = sp.get("laser_direction")
            if origin and direction:
                issues = laser_path_issues(origin, direction, sp)
                if issues:
                    safety_note = (
                        "\n\nLASER SAFETY CHECK FAILED — REFUSE THIS PATH. "
                        f"Issues: {'; '.join(issues)}."
                    )
                else:
                    safety_note = "\n\nLASER SAFETY CHECK PASSED — path clear."
            else:
                safety_note = (
                    "\n\nLaser requested but no origin/direction supplied."
                )

        system_prompt = PROMPTS.get(name, "")
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({
            "role": "user",
            "content": (
                f"Spatial context:\n{spatial_context_text(sp)}\n\n"
                f"{user_input}{safety_note}"
            ),
        })

        try:
            llm = get_llm(settings, system_prompt)
            content = _invoke_with_retry(llm, messages)
        except Exception as e:
            logger.error("%s failed: %s", name, e, exc_info=True)
            content = f"[{name}] error: {e}"
        return {"response": content, "route": name}

    return node


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("director", _director_node())
    for name in VALID_ROUTES:
        g.add_node(name, _specialist_node(name))
    g.set_entry_point("director")
    g.add_conditional_edges(
        "director",
        lambda s: s.get("route", "assistant"),
        {n: n for n in VALID_ROUTES},
    )
    for n in VALID_ROUTES:
        g.add_edge(n, END)
    return g.compile()


# ----------------------------------------------------------------------
# RAG marker resolution (local ChromaDB, no API key needed)
# ----------------------------------------------------------------------

RAG_PATTERN = re.compile(r"\[RAG:\s*(.+?)\s*\]")


def resolve_rag_markers(text: str, n_results: int = 3) -> str:
    """Replace every [RAG: query] with the locally-retrieved chunks."""

    def _sub(match: re.Match) -> str:
        query = match.group(1).strip()
        try:
            # Local ChromaDB lookup — no API key required.
            hits = search_knowledge_base(query, n_results=n_results)
        except Exception:
            logger.exception("RAG search failed for query %r", query)
            hits = []
        if not hits:
            return f"[RAG: {query}]\n(no results in knowledge base)"
        joined = "\n---\n".join(hits)
        return f"[RAG: {query}]\n{joined}"

    return RAG_PATTERN.sub(_sub, text)