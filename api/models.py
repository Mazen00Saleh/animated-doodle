"""api.models

Pydantic v2 request and response schemas for the FastAPI backend.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class StartSessionRequest(BaseModel):
    condition: str = Field(..., description="Patient condition, e.g. 'depression'")
    language: str = Field("English", description="Language for patient responses: 'English' or 'Arabic'")


class StartSessionResponse(BaseModel):
    session_id: str
    condition: str
    language: str
    expires_at: Optional[str] = None  # ISO timestamp when session will expire


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., description="UUID returned by /chat/start")
    message: str = Field(..., description="The trainee's message to the simulated patient")
    model: Optional[str] = Field(None, description="Override patient simulator model (uses default if omitted)")
    reasoning_effort: Optional[str] = Field(None, description="Override reasoning effort: low | medium | high")


class ChatMessageResponse(BaseModel):
    session_id: str
    role: str = "assistant"
    content: str


class DeleteSessionResponse(BaseModel):
    session_id: str
    deleted: bool


# ---------------------------------------------------------------------------
# Session timer / results
# ---------------------------------------------------------------------------

class SessionTimeResponse(BaseModel):
    session_id: str
    remaining_seconds: float
    expired: bool


class SessionResultsResponse(BaseModel):
    session_id: str
    strengths: List[str]
    weaknesses: List[str]
    improvement: str


# ---------------------------------------------------------------------------
# Patient Evaluation
# ---------------------------------------------------------------------------

class PatientEvalRequest(BaseModel):
    session_id: str
    role_adherence_threshold: float = Field(0.8, ge=0.0, le=1.0)
    convo_quality_threshold: float = Field(0.7, ge=0.0, le=1.0)


class PatientEvalMetric(BaseModel):
    name: str
    class_name: str = Field(alias="class")
    score: Optional[float]
    threshold: Optional[float]
    passed: bool
    reason: Optional[str] = ""

    model_config = ConfigDict(populate_by_name=True)


class PatientEvalResponse(BaseModel):
    session_id: str
    condition: str
    language: str
    metrics: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Trainee Evaluation
# ---------------------------------------------------------------------------

class TraineeEvalRequest(BaseModel):
    session_id: str
    rubric_path: Optional[str] = Field(None, description="Path to rubric JSON (uses default if omitted)")
    # Judge config overrides (all optional)
    model: Optional[str] = Field(None, description="Groq judge model")
    strict_schema: bool = Field(True, description="Use strict JSON schema mode")
    seed: int = Field(42, ge=0)
    reasoning_effort: Optional[str] = Field("medium", description="none | low | medium | high")
    max_completion_tokens: int = Field(1400, ge=100)


class TraineeEvalResponse(BaseModel):
    session_id: str
    rubric_id: str
    rubric_version: str
    total_score: float
    total_possible: float
    percent: float
    passed: bool = Field(alias="pass")
    min_percent: float
    flags: List[Dict[str, Any]]
    items: List[Dict[str, Any]]
    summary_feedback: List[str]
    judge_meta: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# Rubric
# ---------------------------------------------------------------------------

class RubricResponse(BaseModel):
    rubric_id: str
    version: str
    item_count: int
    pass_criteria: Dict[str, Any]
    items: List[Dict[str, Any]]
