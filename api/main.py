"""api.main

FastAPI application entrypoint.

Run with:
    uvicorn api.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.utils.env import load_env
from api.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load environment variables and initialize DB once at startup."""
    load_env()
    init_db()
    yield


app = FastAPI(
    title="Simulated Patient API",
    description="REST API for the Simulated Patient system.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create frontend directory if it doesn't exist
import os
if not os.path.exists("frontend"):
    os.makedirs("frontend")

# Static files for the frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

# Routers
from api.routes.chat import router as chat_router
from api.routes.patient_eval import router as patient_eval_router
from api.routes.trainee_eval import router as trainee_eval_router
from api.routes.session import router as session_router

API_V1_PREFIX = "/api/v1"

app.include_router(chat_router, prefix=API_V1_PREFIX)
app.include_router(patient_eval_router, prefix=API_V1_PREFIX)
app.include_router(trainee_eval_router, prefix=API_V1_PREFIX)
# session endpoints (timer, results, manual end)
app.include_router(session_router, prefix=API_V1_PREFIX)

@app.get("/health", tags=["Meta"])
def health() -> dict:
    return {"status": "ok"}
