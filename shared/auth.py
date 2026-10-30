"""
Lightman Authentication & Profiles
===================================
Handles user registration, login, session management, and profile storage.

Registration:  username + password -> bcrypt hash -> SQLite (data/users.db)
Login:          session token stored in system keyring
Settings:       per-user JSON profile (data/profiles/<username>.json)

Cross-platform: uses pathlib.Path for all file operations.
"""

from __future__ import annotations

import hmac
import json
import secrets
import sqlite3
import string
from datetime import datetime
from typing import Any, Optional

import bcrypt
import keyring

from shared.config import DATA_DIR, PROFILES_DIR, USERS_DB, get_logger

logger = get_logger("auth")


# ─── Database Initialization ─────────────────────────────────────────

def _init_db() -> None:
    """Initialize the SQLite user database if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_DB.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(USERS_DB))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,  -- bcrypt hash
            salt        TEXT    NOT NULL,  -- bcrypt salt
            api_key     TEXT    UNIQUE NOT NULL,
            created_at  TEXT    NOT NULL,
            last_login  TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.debug("User database initialized at %s", USERS_DB)


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    _init_db()
    conn = sqlite3.connect(str(USERS_DB))
    conn.row_factory = sqlite3.Row
    return conn



# ─── Registration ───────────────────────────────────────────────────

def register_user(username: str, password: str) -> bool:
    """
    Register a new user with bcrypt-hashed password.
    Returns True on success, False if username already exists or input invalid.
    """
    # Validate input
    if not username or not password:
        logger.warning("Registration failed: empty username or password")
        return False

    if len(username) < 3:
        logger.warning("Registration failed: username too short (<3 chars)")
        return False

    if len(password) < 6:
        logger.warning("Registration failed: password too short (<6 chars)")
        return False

    # Sanitize username (alphanumeric + underscore/hyphen)
    allowed = set(string.ascii_letters + string.digits + "_-")
    if not all(c in allowed for c in username):
        logger.warning("Registration failed: username contains invalid characters")
        return False

    # Hash password with bcrypt
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
    api_key = secrets.token_hex(16)

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO users (username, password, salt, api_key, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, hashed, salt.decode("utf-8"), api_key, now),
        )
        conn.commit()
        logger.info("User registered: %s", username)
        return True
    except sqlite3.IntegrityError:
        logger.warning("Registration failed: username '%s' already exists", username)
        return False
    finally:
        conn.close()


# ─── Authentication / Login ─────────────────────────────────────────

def authenticate(username: str, password: str) -> bool:
    """
    Verify username and password using bcrypt.
    Returns True if credentials are valid.
    """
    if not username or not password:
        return False

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row is None:
            logger.warning("Authentication failed: unknown user '%s'", username)
            return False

        stored_hash = row["password"].encode("utf-8")
        password_bytes = password.encode("utf-8")
        valid = bcrypt.checkpw(password_bytes, stored_hash)

        if valid:
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE username = ?",
                (datetime.utcnow().isoformat(), username),
            )
            conn.commit()
            logger.info("User authenticated: %s", username)
        else:
            logger.warning("Authentication failed: bad password for '%s'", username)

        return valid
    finally:
        conn.close()


def generate_session_token() -> str:
    """Generate a cryptographically secure session token."""
    return secrets.token_urlsafe(32)


def login(username: str, password: str) -> Optional[str]:
    """
    Authenticate user and store session token in system keyring.
    Returns the session token on success, None on failure.
    """
    if not authenticate(username, password):
        return None

    token = generate_session_token()
    service_name = "lightman"
    keyring.set_password(service_name, username, token)

    logger.info("User logged in: %s (session stored in keyring)", username)
    return token


def logout(username: str) -> bool:
    """Remove the session token from keyring."""
    service_name = "lightman"
    try:
        keyring.delete_password(service_name, username)
        logger.info("User logged out: %s", username)
        return True
    except KeyError:
        logger.warning("Logout failed: no session for '%s'", username)
        return False


def is_logged_in(username: str) -> bool:
    """Check if the user has an active session in keyring."""
    service_name = "lightman"
    token = keyring.get_password(service_name, username)
    return token is not None



# ─── Profile Management ─────────────────────────────────────────────

def _profile_path(username: str) -> Path:
    """Get the path to a user's profile JSON file."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in username)
    return PROFILES_DIR / f"{safe_name}.json"


def create_default_profile(username: str) -> dict[str, Any]:
    """Create and return a default profile for a new user."""
    return {
        "username": username,
        "display_name": username,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "settings": {
            "mode": "assist",
            "audience": "adults",
            "rtsp_url": "",
            "standby_level": 0.05,
            "intercept_threshold": 0.15,
            "default_universe": 1,
        },
        "consoles": {
            "titan": {"enabled": False, "host": "", "port": 80, "api_key": ""},
            "grandma3": {"enabled": False, "host": "", "port": 6000},
            "chamsys": {"enabled": False, "host": "", "port": 65535},
            "eos": {"enabled": False, "host": "", "port": 1975},
            "qlcplus": {"enabled": False, "host": "", "port": 49064},
        },
        "recent_fixtures": [],
        "knowledge_bases": [],
    }


def save_profile(username: str, profile: dict[str, Any]) -> bool:
    """Save a user's profile to data/profiles/<username>.json."""
    profile["updated_at"] = datetime.utcnow().isoformat()
    path = _profile_path(username)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        logger.debug("Profile saved: %s", path)
        return True
    except Exception as e:
        logger.error("Failed to save profile for '%s': %s", username, e)
        return False


def load_profile(username: str) -> Optional[dict[str, Any]]:
    """
    Load a user's profile from data/profiles/<username>.json.
    If no profile exists, creates a default one.
    """
    path = _profile_path(username)
    if not path.exists():
        profile = create_default_profile(username)
        save_profile(username, profile)
        return profile

    try:
        with path.open("r", encoding="utf-8") as f:
            profile = json.load(f)
        logger.debug("Profile loaded: %s", path)
        return profile
    except Exception as e:
        logger.error("Failed to load profile for '%s': %s", username, e)
        return create_default_profile(username)


def update_profile_setting(username: str, key: str, value: Any) -> bool:
    """
    Update a single setting in the user's profile.
    Key path uses dot notation, e.g. 'settings.mode' or 'consoles.titan.host'.
    """
    profile = load_profile(username)
    if profile is None:
        return False

    keys = key.split(".")
    target = profile
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]
    target[keys[-1]] = value

    return save_profile(username, profile)


# ─── Token Verification ─────────────────────────────────────────────

def verify_session_token(username: str, token: str) -> bool:
    """
    Verify a session token using constant-time comparison.
    """
    service_name = "lightman"
    stored_token = keyring.get_password(service_name, username)
    if stored_token is None:
        return False
    return hmac.compare_digest(stored_token, token)

def get_user_api_key(username: str) -> Optional[str]:
    """Get the saved API key for a user.
    Returns the API key string, or None if user not found.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT api_key FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row["api_key"] if row else None
    finally:
        conn.close()
