"""one-time script: extract data/HistoricalServices/FSR-*.txt into data/processed/reports.csv.
"""
import argparse
import json
from typing import Literal, Optional

import pandas as pd
from openai import OpenAI
from pydantic import BaseModel

from config import MODEL, PROCESSED_DIR, REPORTS_DIR
from prompts import REPORT_EXTRACTION_PROMPT

CACHE_DIR = PROCESSED_DIR / "cache"
OUTPUT_CSV = PROCESSED_DIR / "reports.csv"

# define the equipment types as a Literal type for validation
Equipment = Literal[
    "AC filter",
    "CellStation",
    "ColumnCell",
    "Concorde Cell",
    "Filter Optimizer",
    "FloatForce upgrade",
    "GM filter",
    "Larox PF filter",
    "Larox PF-DS",
    "MD series mill discharge pump",
    "Orion series horizontal slurry pump",
    "SALA VSP-750 sump pump",
    "other",
]

# define the structure of a service report 
class ServiceReport(BaseModel):
    report_id: str
    customer: Optional[str]
    site: Optional[str]
    country: Optional[str]
    visit_date: Optional[str]
    technician: Optional[str]
    equipment: Equipment
    task_summary: str
    onsite_hours: Optional[float]
    travel_hours: Optional[float]
    labour_rate: Optional[float]
    travel_rate: Optional[float]
    parts_cost: Optional[float]
    total_cost: Optional[float]
    currency: Optional[Literal["USD", "EUR", "CAD", "AUD", "SEK", "ZAR"]]
    weekend_or_overtime: bool
    cost_status: Literal["itemized", "total_only", "none"]


def extract(client: OpenAI, text: str) -> ServiceReport:
    """extract structured data from a service report text using the OpenAI API"""
    response = client.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": REPORT_EXTRACTION_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format=ServiceReport,
    )
    return response.choices[0].message.parsed


def load_or_extract(client: OpenAI, path, force: bool) -> dict:
    """load a cached report if available, otherwise extract and cache it"""
    cache_file = CACHE_DIR / f"{path.stem}.json"
    if cache_file.exists() and not force:
        return json.loads(cache_file.read_text(encoding="utf-8"))

    report = extract(client, path.read_text(encoding="utf-8"))
    report.report_id = path.stem  # filename is the reliable ID
    data = report.model_dump()
    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def consistency_check(row: dict) -> Optional[bool]:
    """onsite*labour_rate + travel*travel_rate + parts ~= total (1% tolerance). None if not checkable."""
    needed = ["onsite_hours", "labour_rate", "travel_hours", "travel_rate", "total_cost"]
    if any(row.get(k) is None for k in needed) or not row["total_cost"]:
        return None
    expected = (
        row["onsite_hours"] * row["labour_rate"]
        + row["travel_hours"] * row["travel_rate"]
        + (row.get("parts_cost") or 0)
    )
    return abs(expected - row["total_cost"]) <= 0.01 * row["total_cost"]


def main():
    """main function to parse reports and save to CSV"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="ignore cache and re-call the API")
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    client = OpenAI()

    rows = []
    for path in sorted(REPORTS_DIR.glob("FSR-*.txt")):
        print(f"{path.stem} ...", flush=True)
        row = load_or_extract(client, path, args.force)
        row["check_ok"] = consistency_check(row)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(df)} rows to {OUTPUT_CSV}\n")

    print("Rows per equipment:")
    print(df["equipment"].value_counts().to_string(), "\n")
    print("Rows per cost_status:")
    print(df["cost_status"].value_counts().to_string(), "\n")
    print("check_ok:")
    print(df["check_ok"].value_counts(dropna=False).to_string(), "\n")

    failed = df[df["check_ok"] == False]  # noqa: E712
    cols = ["report_id", "onsite_hours", "labour_rate", "travel_hours", "travel_rate",
            "parts_cost", "total_cost", "currency", "weekend_or_overtime"]
    if failed.empty:
        print("No failed checks.")
    else:
        print("Failed checks:")
        print(failed[cols].to_string(index=False))

    no_currency = df[df["total_cost"].notna() & df["currency"].isna()]
    if not no_currency.empty:
        print("\nCost stated but currency not explicit:", ", ".join(no_currency["report_id"]))


if __name__ == "__main__":
    main()
