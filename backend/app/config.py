"""Runtime configuration. Everything can be overridden with environment variables (see .env.example)."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:  # dotenv is optional
    pass

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "YTL_TrackA_Udyam_Digital_Data"))
DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).resolve().parents[1] / "udyam.db"))

# The case fixes "today" for every date-based rule (e.g. address proof <= 90 days old).
TODAY = date.fromisoformat(os.getenv("APP_TODAY", "2026-07-15"))

GST_RATE = 0.18
ADDRESS_PROOF_MAX_AGE_DAYS = 90

# Any OpenAI-compatible endpoint works (OpenAI, Gemini, Groq, OpenRouter, Ollama, ...).
# When LLM_API_KEY is empty the app runs on its deterministic fallback.
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or None
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_VISION_MODEL = os.getenv("LLM_VISION_MODEL", LLM_MODEL)
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "30"))

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

CONSENT_VERSION = "2026-07-v1"
KYC_RETENTION_DAYS = 180  # extracted, verified fields; raw images are never persisted
