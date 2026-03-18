"""src.patient_sim.interfaces

Interfaces for patient simulation providers.

This makes it easy to swap Groq/OpenAI/local models without touching Streamlit UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


Conversation = List[Dict[str, str]]


@dataclass
class PatientProfile:
    condition: str
    language: str

    # Demographics
    age: int = 35
    gender: str = "unspecified"
    occupation: str = "unspecified"

    # Clinical content
    chief_complaint: str = ""
    symptom_onset: str = ""
    symptom_severity: str = "moderate"        # mild | moderate | severe
    relevant_life_events: List[str] = field(default_factory=list)
    past_psychiatric_history: str = ""
    current_medications: List[str] = field(default_factory=list)
    substance_use: str = ""

    # Risk (deterministic flag — drives rubric gate patient_risk_positive)
    risk_positive: bool = False
    risk_detail: str = ""

    # Behavioral style
    response_style: str = "terse"             # terse | normal | verbose
    emotional_tone: str = "flat"              # flat | anxious | guarded | tearful | irritable

    # Disclosure model
    freely_disclose: List[str] = field(default_factory=list)
    disclose_if_asked: List[str] = field(default_factory=list)
    resist_disclosing: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PatientSimConfig:
    model: str = "openai/gpt-oss-120b"
    temperature: float = 1.0
    max_completion_tokens: int = 8192
    top_p: float = 1.0
    reasoning_effort: str = "medium"
    reasoning_format: str | None = None


class PatientSimulator(Protocol):
    def generate(self, conversation: Conversation, *, config: PatientSimConfig) -> str:
        """Generate the next patient message given the full conversation."""
        ...
