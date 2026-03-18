"""api.database

Built-in SQLite database handler.
Using standard library sqlite3 to save disk space.
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).resolve().parents[1] / "simulated_patient.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tables for Sessions
    # add an expires_at column so we can impose a 10‑minute timer per session
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            condition TEXT NOT NULL,
            language TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')
    # if the table already existed before adding expires_at, add the column now
    cursor.execute("PRAGMA table_info(sessions)")
    cols = [row['name'] for row in cursor.fetchall()]
    if 'expires_at' not in cols:
        cursor.execute("ALTER TABLE sessions ADD COLUMN expires_at TIMESTAMP")
    if 'profile' not in cols:
        cursor.execute("ALTER TABLE sessions ADD COLUMN profile TEXT")
    
    # Table for Messages (The Memory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    ''')
    
    # Table for Evaluations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            eval_type TEXT NOT NULL, -- 'patient' or 'trainee'
            score_data TEXT NOT NULL,  -- JSON blob of the result
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# CRUD Helpers
def save_session(session_id: str, condition: str, language: str, profile_json: str = None):
    """Add a new session and record when it should expire (10 minutes from creation)."""
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO sessions (session_id, condition, language, expires_at, profile) VALUES (?, ?, ?, ?, ?)",
        (session_id, condition, language, expires_at.isoformat(), profile_json),
    )
    conn.commit()
    conn.close()

def get_session_profile(session_id: str):
    """
    Return a PatientProfile dataclass for a session, or None if not available.
    """
    import json as _json
    from src.patient_sim.interfaces import PatientProfile
    conn = get_db_connection()
    row = conn.execute(
        "SELECT condition, language, profile FROM sessions WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    conn.close()
    if not row or not row["profile"]:
        return None
    try:
        data = _json.loads(row["profile"])
        # Remove condition/language if they were serialized into the blob
        data.pop("condition", None)
        data.pop("language", None)
        return PatientProfile(
            condition=row["condition"],
            language=row["language"],
            **data
        )
    except Exception:
        return None

def add_message(session_id: str, role: str, content: str):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

def get_session_history(session_id: str):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [{"role": row["role"], "content": row["content"]} for row in rows]

def get_session_info(session_id: str):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM sessions WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    info = {k: row[k] for k in row.keys()}
    # convert timestamp string back to datetime
    if info.get("expires_at"):
        try:
            info["expires_at"] = datetime.fromisoformat(info["expires_at"])
        except Exception:
            # leave as string if parsing fails
            pass
    return info

def save_evaluation(session_id: str, eval_type: str, score_data: dict):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO evaluations (session_id, eval_type, score_data) VALUES (?, ?, ?)",
        (session_id, eval_type, json.dumps(score_data))
    )
    conn.commit()
    conn.close()

def delete_session_data(session_id: str):
    conn = get_db_connection()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM evaluations WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


# ----------------------------------------------------------
# Timer helpers
# ----------------------------------------------------------

def is_session_active(session_id: str) -> bool:
    """Return True if the session exists and has not expired yet."""
    info = get_session_info(session_id)
    if info is None:
        return False
    expires = info.get("expires_at")
    if not expires:
        return True
    return datetime.utcnow() < expires


def time_left_seconds(session_id: str) -> float:
    """Return number of seconds remaining, or 0 if expired/missing."""
    info = get_session_info(session_id)
    if info is None or not info.get("expires_at"):
        return 0.0
    delta = info["expires_at"] - datetime.utcnow()
    return max(0.0, delta.total_seconds())


# ----------------------------------------------------------
# Results helpers (stubbed for frontend use)
# ----------------------------------------------------------

def get_latest_trainee_eval(session_id: str):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT score_data FROM evaluations WHERE session_id = ? AND eval_type = 'trainee' ORDER BY created_at DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    try:
        return json.loads(row["score_data"])
    except Exception:
        return None


def compute_session_results(session_id: str) -> dict:
    """Generate strengths/weaknesses/improvement text from the latest trainee evaluation.

    This is a minimal implementation that the frontend can call immediately.  It
    returns a dictionary with keys `strengths`, `weaknesses`, and `improvement`.
    """
    eval_data = get_latest_trainee_eval(session_id)
    strengths: list[str] = []
    weaknesses: list[str] = []
    if eval_data and isinstance(eval_data, dict):
        for item in eval_data.get("items", []):
            desc = item.get("desc") or item.get("id")
            if item.get("achieved"):
                strengths.append(desc)
            else:
                weaknesses.append(desc)
    improvement = "Review the items you missed and seek feedback from an examiner."
    return {"strengths": strengths, "weaknesses": weaknesses, "improvement": improvement}
