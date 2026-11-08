"""Central configuration. Values can be overridden with environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EVAL_DATA_DIR = DATA_DIR / "eval"
DB_PATH = PROCESSED_DIR / "olist.duckdb"
RESULTS_DIR = ROOT / "results"
REPORTS_DIR = RESULTS_DIR / "reports"
TRACES_DIR = RESULTS_DIR / "traces"

# LLM
KPI_MODEL = os.getenv("KPI_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_TEMPERATURE = 0.0
LLM_SEED = 42
LLM_NUM_CTX = 16384

# Analysis window (confirmed from monthly order counts, see docs/DECISIONS.md)
WINDOW_START = "2017-01"
WINDOW_END = "2018-08"

# Detection thresholds
Z_THRESHOLD = 2.0
PCT_THRESHOLD = 0.15
TRAILING_MONTHS = 6

# Agent loop
MAX_AGENT_STEPS = 12
MAX_SQL_ERRORS_PER_HYPOTHESIS = 2

# SQL guard
SQL_MAX_ROWS = 200
SQL_TIMEOUT_S = 10

# Verifier
VERIFY_REL_TOL = 0.01

# Decomposition
TOP_SEGMENTS = 10
