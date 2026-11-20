# multimodal_suite/db.py
"""SQLite‑based lightweight database utilities for the suite.
Provides a simple ``Campaign`` dataclass and CRUD helpers without external
dependencies.
"""

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Campaign:
    id: int
    name: str
    description: str
    brief: Optional[str]
    created_at: str


@dataclass
class User:
    id: int
    email: str
    display_name: str
    created_at: str

# ---------------------------------------------------------------------------
# Database path – placed in the project root.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "campaigns.sqlite"

# ---------------------------------------------------------------------------
# Initialise the SQLite file and ensure the table exists.
# ---------------------------------------------------------------------------

def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            brief TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS remember_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()

_init_db()

# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def _serialize_brief(brief: Any) -> Optional[str]:
    """SQLite only accepts strings/numbers; Gemini briefs arrive as dicts."""
    if brief is None:
        return None
    if isinstance(brief, (dict, list)):
        return json.dumps(brief)
    return str(brief)


def save_campaign(name: str, description: str, brief: Optional[Any] = None) -> Campaign:
    """Insert a new campaign and return a ``Campaign`` instance."""
    brief_text = _serialize_brief(brief)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO campaigns (name, description, brief, created_at) VALUES (?, ?, ?, ?)",
        (name, description, brief_text, datetime.utcnow().isoformat()),
    )
    conn.commit()
    campaign_id = cur.lastrowid
    conn.close()
    return Campaign(
        id=campaign_id,
        name=name,
        description=description,
        brief=brief_text,
        created_at=datetime.utcnow().isoformat(),
    )


def get_all_campaigns() -> List[Campaign]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, brief, created_at FROM campaigns ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [Campaign(id=row[0], name=row[1], description=row[2], brief=row[3], created_at=row[4]) for row in rows]


def get_campaign_by_id(campaign_id: int) -> Optional[Campaign]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, description, brief, created_at FROM campaigns WHERE id = ?",
        (campaign_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return Campaign(id=row[0], name=row[1], description=row[2], brief=row[3], created_at=row[4])
    return None

# ---------------------------------------------------------------------------
# Authentication helpers (PBKDF2-SHA256, never store plain-text passwords)
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 210_000
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_REMEMBER_DAYS = 30


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_email(email: str) -> Optional[str]:
    value = normalize_email(email)
    if not value:
        return "Please enter your email address."
    if not _EMAIL_RE.match(value):
        return "Please enter a valid email address, for example you@company.com."
    return None


def validate_password(password: str, confirm: Optional[str] = None) -> Optional[str]:
    if not password:
        return "Please enter a password."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if confirm is not None and password != confirm:
        return "Passwords do not match. Please re-enter them."
    return None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        _algo, iterations, salt_hex, digest_hex = stored_hash.split("$")
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _row_to_user(row: Tuple[Any, ...]) -> User:
    return User(id=row[0], email=row[1], display_name=row[2] or row[1], created_at=row[3])


def create_user(email: str, password: str, display_name: str = "") -> User:
    email_error = validate_email(email)
    if email_error:
        raise ValueError(email_error)
    password_error = validate_password(password)
    if password_error:
        raise ValueError(password_error)

    email_value = normalize_email(email)
    name_value = (display_name or "").strip() or email_value.split("@")[0]
    created_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (email, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
            (email_value, hash_password(password), name_value, created_at),
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError as exc:
        conn.close()
        raise ValueError("An account with this email already exists. Try signing in instead.") from exc
    conn.close()
    return User(id=user_id, email=email_value, display_name=name_value, created_at=created_at)


def authenticate_user(email: str, password: str) -> Optional[User]:
    email_value = normalize_email(email)
    if not email_value or not password:
        return None
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, display_name, created_at, password_hash FROM users WHERE email = ?",
        (email_value,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if not verify_password(password, row[4]):
        return None
    return _row_to_user(row[:4])


def get_user_by_id(user_id: int) -> Optional[User]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, display_name, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return _row_to_user(row)
    return None


def _token_digest(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_remember_token(user_id: int) -> str:
    raw_token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=_REMEMBER_DAYS)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO remember_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, _token_digest(raw_token), expires_at),
    )
    conn.commit()
    conn.close()
    return raw_token


def user_from_remember_token(raw_token: Optional[str]) -> Optional[User]:
    if not raw_token:
        return None
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT u.id, u.email, u.display_name, u.created_at, t.expires_at, t.id
        FROM remember_tokens t
        JOIN users u ON u.id = t.user_id
        WHERE t.token_hash = ?
        """,
        (_token_digest(raw_token),),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    expires_at = row[4]
    token_id = row[5]
    if expires_at < datetime.utcnow().isoformat():
        cur.execute("DELETE FROM remember_tokens WHERE id = ?", (token_id,))
        conn.commit()
        conn.close()
        return None
    conn.close()
    return _row_to_user(row[:4])


def revoke_remember_token(raw_token: Optional[str]) -> None:
    if not raw_token:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM remember_tokens WHERE token_hash = ?", (_token_digest(raw_token),))
    conn.commit()
    conn.close()


# Exported symbols for convenience when importing *
__all__ = [
    "Campaign",
    "User",
    "save_campaign",
    "get_all_campaigns",
    "get_campaign_by_id",
    "create_user",
    "authenticate_user",
    "get_user_by_id",
    "create_remember_token",
    "user_from_remember_token",
    "revoke_remember_token",
    "validate_email",
    "validate_password",
    "normalize_email",
]
