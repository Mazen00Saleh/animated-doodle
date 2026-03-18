"""api.dependencies

FastAPI dependency-injection providing app-lifetime singletons for the
patient simulator, patient evaluator, and trainee evaluation pipeline.
"""

from __future__ import annotations

from functools import lru_cache

from src.evaluation.patient.deepeval_patient import DeepEvalPatientEvaluator
from src.evaluation.trainee.pipeline import TraineeEvalPipeline
from src.patient_sim.groq_patient_sim import GroqPatientSimulator
from src.trainee_judge.trainee_judge_groq import judge_trainee_with_groq
from src.trainee_judge.trainee_judge_schema import load_rubric as load_examiner_rubric
from src.trainee_judge.trainee_score import score_from_judge_output


@lru_cache(maxsize=1)
def get_patient_simulator() -> GroqPatientSimulator:
    return GroqPatientSimulator()


@lru_cache(maxsize=1)
def get_patient_evaluator() -> DeepEvalPatientEvaluator:
    return DeepEvalPatientEvaluator()


@lru_cache(maxsize=1)
def get_trainee_pipeline() -> TraineeEvalPipeline:
    return TraineeEvalPipeline(
        rubric_loader=load_examiner_rubric,
        judge_fn=judge_trainee_with_groq,
        scorer_fn=score_from_judge_output,
    )
