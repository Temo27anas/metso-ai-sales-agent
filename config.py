import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# define data directories
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = DATA_DIR / "HistoricalServices"
BROCHURES_DIR = DATA_DIR / "brochures"
FLOTATION_CSV = DATA_DIR / "flotation_process_data_hourly.csv"
PROCESSED_DIR = DATA_DIR / "processed"

# define LLM model
MODEL = os.getenv("OPENAI_MODEL") or "gpt-6-luna"
# Chat Completions (gpt-6-luna) only allows function tools on reasoning models with effort "none".
# Set OPENAI_REASONING_EFFORT= (empty) for models that don't accept the parameter.
REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "none") or None
