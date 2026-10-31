"""
Lightman — simple file-based auth.

Storage: data/users.json
Hash:    bcrypt if installed, sha256 fallback.
"""

import os
import sys
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


def _project_root() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _users_path() -> str:
    d = os.path.join(_project_root(), "data")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "users.json")


def _hash_password(password: str) -> str:
    try:
        import bcrypt
        return bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    except ImportError:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_password(password: str, stored: str) -> bool:
    if not isinstance(stored, str) or not stored:
        return False
    if stored.startswith("$2"):
        try:
            import bcrypt
            return bcrypt.checkpw(
                password.encode("utf-8"), stored.encode("utf-8")
            )
        except Exception as e:
            logger.error("bcrypt verify failed: %s", e)
            return False
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored


def _load_users() -> dict:
    path = _users_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning("users.json is not a dict — resetting")
            return {}
        return data
    except Exception as e:
        logger.error("users.json read failed (%s) — resetting", e)
        return {}


def _save_users(users: dict) -> None:
    path = _users_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
        logger.info("users.json saved (%d accounts)", len(users))
    except Exception as e:
        logger.error("users.json write failed: %s", e)
        raise


def ensure_default_user() -> None:
    """Create admin/admin if the file is missing, empty or corrupted."""
    users = _load_users()
    if not users or "admin" not in users:
        users["admin"] = _hash_password("admin")
        _save_users(users)
        logger.warning(
            "Default admin account created (login: admin / admin). "
            "Change the password after first login."
        )


def authenticate(username: str, password: str) -> bool:
    if not username or not password:
        return False
    users = _load_users()
    if not users:
        ensure_default_user()
        users = _load_users()
    stored = users.get(username)
    if not stored:
        return False
    return _verify_password(password, stored)


def register_user(username: str, password: str) -> bool:
    if not username or not password:
        return False
    if len(username) < 2 or len(password) < 3:
        return False
    users = _load_users()
    if username in users:
        return False
    users[username] = _hash_password(password)
    _save_users(users)
    return True


def reset_database() -> None:
    """Wipe the users DB and recreate admin/admin."""
    path = _users_path()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error("Failed to remove users.json: %s", e)
    ensure_default_user()