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