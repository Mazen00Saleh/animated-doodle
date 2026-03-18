"""api.session

In-memory session store for the FastAPI backend.

Each session holds:
  - conversation_history: list of {role, content} dicts
  - active_condition: the patient condition string
  - active_language: response language

Sessions expire after TTL_SECONDS of inactivity.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, List, Optional

TTL_SECONDS = 7200  # 2 hours


class _Session:
    def __init__(self, condition: str, language: str, history: List[Dict[str, str]]) -> None:
        self.condition = condition
        self.language = language
        self.history: List[Dict[str, str]] = history
        self.last_accessed = time.monotonic()

    def touch(self) -> None:
        self.last_accessed = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.last_accessed) > TTL_SECONDS


class SessionStore:
    """Thread-safe in-memory session store."""

    def __init__(self) -> None:
        self._sessions: Dict[str, _Session] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def create(self, condition: str, language: str, history: List[Dict[str, str]]) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._sessions[session_id] = _Session(condition, language, history)
        return session_id

    def get(self, session_id: str) -> Optional[_Session]:
        """Return the session if it exists and is not expired, else None."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.is_expired():
                del self._sessions[session_id]
                return None
            session.touch()
            return session

    def delete(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def purge_expired(self) -> int:
        """Remove all expired sessions. Returns count removed."""
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
            for sid in expired:
                del self._sessions[sid]
        return len(expired)

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------
    def append_message(self, session_id: str, role: str, content: str) -> None:
        session = self.get(session_id)
        if session is None:
            raise KeyError(f"Session not found or expired: {session_id}")
        with self._lock:
            session.history.append({"role": role, "content": content})

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        session = self.get(session_id)
        if session is None:
            raise KeyError(f"Session not found or expired: {session_id}")
        return list(session.history)

    def is_conversation_ready(self, session_id: str, min_turns: int = 2) -> bool:
        """Return True if the conversation has at least min_turns non-system messages."""
        try:
            history = self.get_history(session_id)
        except KeyError:
            return False
        non_system = [m for m in history if m.get("role") != "system"]
        return len(non_system) >= min_turns


# Module-level singleton used by the FastAPI app.
store = SessionStore()
