"""src.patient_sim.groq_patient_sim

Groq-backed patient simulator.

This is a thin wrapper around Groq Chat Completions.
"""

from __future__ import annotations

import os
from typing import Optional

from groq import Groq

from src.patient_sim.interfaces import Conversation, PatientProfile, PatientSimConfig


class GroqPatientSimulator:
    def __init__(self, *, api_key: Optional[str] = None) -> None:
        self._client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))

    def generate_profile(self, condition: str, language: str) -> PatientProfile:
        """
        Makes a single LLM call to generate a random PatientProfile for a session.
        Uses a cheaper/faster model since this is a structured generation task.
        Falls back to a minimal default PatientProfile if parsing fails.

        Retries up to 3 times on API errors with exponential backoff.
        Higher temperature (1.5) increases diversity/creativity of profiles.
        """
        import json
        import time
        import re
        from src.patient_sim.prompts import build_profile_generation_prompt

        system_prompt = build_profile_generation_prompt(condition, language)
        max_retries = 3

        for attempt in range(max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": (
                                f"Generate a patient profile for the condition: {condition}, "
                                f"responding in {language}. Return ONLY valid JSON, no markdown."
                            ),
                        },
                    ],
                    temperature=1.5,  # Increased for more diverse profiles
                    max_completion_tokens=1024,
                    stream=False,
                )

                raw = resp.choices[0].message.content.strip()

                # Try to extract JSON from various formats
                # Try markdown code blocks first
                if "```" in raw:
                    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
                    if match:
                        raw = match.group(1).strip()
                
                # Try to find JSON object within text
                if not raw.startswith("{"):
                    match = re.search(r"\{.*\}", raw, re.DOTALL)
                    if match:
                        raw = match.group(0).strip()

                data = json.loads(raw)

                return PatientProfile(
                    condition=condition,
                    language=language,
                    age=int(data.get("age", 35)),
                    gender=str(data.get("gender", "unspecified")),
                    occupation=str(data.get("occupation", "unspecified")),
                    chief_complaint=str(data.get("chief_complaint", "")),
                    symptom_onset=str(data.get("symptom_onset", "")),
                    symptom_severity=str(data.get("symptom_severity", "moderate")),
                    relevant_life_events=list(data.get("relevant_life_events", [])),
                    past_psychiatric_history=str(
                        data.get("past_psychiatric_history", "")
                    ),
                    current_medications=list(data.get("current_medications", [])),
                    substance_use=str(data.get("substance_use", "")),
                    risk_positive=bool(data.get("risk_positive", False)),
                    risk_detail=str(data.get("risk_detail", "")),
                    response_style=str(data.get("response_style", "terse")),
                    emotional_tone=str(data.get("emotional_tone", "flat")),
                    freely_disclose=list(data.get("freely_disclose", [])),
                    disclose_if_asked=list(data.get("disclose_if_asked", [])),
                    resist_disclosing=list(data.get("resist_disclosing", [])),
                )

            except json.JSONDecodeError as e:
                error_msg = f"JSON parse error on attempt {attempt + 1}/{max_retries}: {e}"
                print(error_msg)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue

            except Exception as e:
                error_msg = (
                    f"Error generating patient profile on attempt {attempt + 1}/{max_retries}: {e}"
                )
                print(error_msg)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue

        # All retries exhausted: graceful fallback
        print(
            f"Failed to generate profile for {condition}/{language} after {max_retries} attempts. "
            "Using default profile."
        )
        return PatientProfile(condition=condition, language=language)

    def generate(self, conversation: Conversation, *, config: PatientSimConfig) -> str:
        resp = self._client.chat.completions.create(
            model=config.model,
            messages=conversation,
            temperature=config.temperature,
            max_completion_tokens=config.max_completion_tokens,
            top_p=config.top_p,
            reasoning_effort=config.reasoning_effort,
            reasoning_format=config.reasoning_format,
            stream=False,
            stop=None,
        )
        return resp.choices[0].message.content
