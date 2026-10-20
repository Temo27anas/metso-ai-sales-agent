"""Tools the assistant can call. Every number the assistant states comes from here."""
import json
from typing import Optional, get_args

import pandas as pd

from config import BROCHURES_DIR, FLOTATION_CSV, PROCESSED_DIR
from parse_reports import Equipment
from prompts import list_brochures

REPORTS_CSV = PROCESSED_DIR / "reports.csv"
EQUIPMENT_NAMES = [e for e in get_args(Equipment) if e != "other"]
MIN_REPORTS_FOR_CONFIDENCE = 3


# ==  Brochures ==
def get_brochure(product: str) -> dict:
    """return the full text of one product brochure, or an error if not found"""
    path = BROCHURES_DIR / f"{product}.md"
    if not path.exists():
        return {"error": f"No brochure named '{product}'.", "available": list(list_brochures())}
    return {"product": product, "text": path.read_text(encoding="utf-8")}



# ==  Service costs ==
def estimate_service_cost(equipment: str, country: Optional[str] = None) -> dict:
    """return cost and hours from historical field service reports for one equipment type,
    plus labour/travel rates seen in `country` (any equipment) if given"""
    df = pd.read_csv(REPORTS_CSV)
    # labour + travel + parts, computed here so the LLM never does arithmetic
    df["line_item_sum"] = (df["onsite_hours"] * df["labour_rate"]
                           + df["travel_hours"] * df["travel_rate"]
                           + df["parts_cost"].fillna(0)).round(2)
    rows = df[df["equipment"] == equipment] # filter to the requested equipment
    if rows.empty:
        result = {"equipment": equipment, "reports_found": 0,
                  "note": "No service history for this equipment."} # no data for this equipment
        if country:
            result["country_rates"] = _country_rates(df, country)
        return result

    costed = rows[rows["total_cost"].notna()]
    result = {
        "equipment": equipment,
        "reports_found": len(rows),
        "reports_with_cost": len(costed),
        "reports_without_cost": rows.loc[rows["total_cost"].isna(), "report_id"].tolist(),
        "onsite_hours": _range(rows["onsite_hours"]),
        "travel_hours": _range(rows["travel_hours"]),
        "costs_by_currency": {},
        "reports": _records(rows[["report_id", "country", "task_summary", "onsite_hours", "travel_hours",
                                  "labour_rate", "travel_rate", "parts_cost", "line_item_sum",
                                  "total_cost", "currency", "cost_status", "weekend_or_overtime"]]),
        "notes": [],
    }

    # currencies are not converted: no exchange rates in the data.
    for currency, group in costed.groupby("currency"):
        result["costs_by_currency"][currency] = {
            "reports": group["report_id"].tolist(),
            "total_cost": _range(group["total_cost"]),
            "labour_rate": _range(group["labour_rate"]),
            "travel_rate": _range(group["travel_rate"]),
        }

    # add notes about data quality and confidence
    if costed.empty:
        result["notes"].append("No report for this equipment states a cost.")
    for currency, info in result["costs_by_currency"].items():
        n = len(info["reports"])
        if n < MIN_REPORTS_FOR_CONFIDENCE:
            result["notes"].append(f"Low confidence in {currency}: only {n} report(s) with a cost.")
    if costed["currency"].nunique() > 1:
        result["notes"].append("Costs are in several currencies and are not converted.")
    for _, r in costed.iterrows():
        if r["weekend_or_overtime"]:
            result["notes"].append(f"{r['report_id']} was a weekend/overtime visit (higher rate).")
        if r["check_ok"] is False or r["check_ok"] == "False":
            result["notes"].append(f"{r['report_id']}: line items do not add up to the total.")
    for _, r in rows[rows["total_cost"].isna() & rows["line_item_sum"].notna()].iterrows():
        result["notes"].append(
            f"{r['report_id']} states no total; line_item_sum ({r['line_item_sum']} {r['currency']}) "
            "is labour + travel + parts computed from its stated hours, rates and parts.")
    if country:
        result["country_rates"] = _country_rates(df, country)
    return result


def _country_rates(df: pd.DataFrame, country: str) -> dict:
    """labour/travel rates from all reports in one country, any equipment"""
    rows = df[df["country"].str.lower() == country.lower()]
    if rows.empty:
        return {"country": country, "reports_found": 0, "note": "No service reports from this country."}
    rated = rows[rows["labour_rate"].notna() | rows["travel_rate"].notna()]
    return {
        "country": country,
        "reports_found": len(rows),
        "equipment_in_reports": sorted(rows["equipment"].unique()),
        "currencies": sorted(rows["currency"].dropna().unique()),
        "rates_by_currency": {
            currency: {"reports": g["report_id"].tolist(),
                       "labour_rate": _range(g["labour_rate"]),
                       "travel_rate": _range(g["travel_rate"]),
                       "travel_hours": _range(g["travel_hours"])}
            for currency, g in rated.groupby("currency")
        },
        "note": "Rates from visits to other equipment in this country; use as context only.",
    }


def _records(df: pd.DataFrame) -> list[dict]:
    """rows as dicts, with NaN replaced by None so the JSON is clean"""
    return df.astype(object).where(df.notna(), None).to_dict("records")


def _range(series: pd.Series) -> Optional[dict]:
    """return min, median, max, and count of a numeric series, or None if empty"""
    s = series.dropna()
    if s.empty:
        return None
    return {"min": round(s.min(), 2), "median": round(s.median(), 2),
            "max": round(s.max(), 2), "n": int(s.size)}


# == Flotation ==

IRON = "% Iron Concentrate"
SILICA = "% Silica Concentrate"

def assess_flotation(silica_concentrate: Optional[float] = None,
                     iron_concentrate: Optional[float] = None) -> dict:
    """Compare a customer's iron ore flotation concentrate grades against hourly plant data (percentiles),
    and provide insights into the performance of the flotation process."""
    df = pd.read_csv(FLOTATION_CSV)
    result = {
        "data": {"rows": len(df), "from": df["date"].min(), "to": df["date"].max()},
        "plant_distribution": {
            col: {q: round(df[col].quantile(p), 2)
                  for q, p in [("p10", .1), ("p25", .25), ("p50", .5), ("p75", .75), ("p90", .9)]}
            for col in (IRON, SILICA)
        },
    }

    # Percentile = share of plant hours with a value at or below the value of customer
    if silica_concentrate is not None:
        pct = (df[SILICA] <= silica_concentrate).mean() * 100
        result["silica"] = {"value": silica_concentrate, "percentile": round(pct, 1),
                            "share_of_hours_with_lower_silica": round(pct, 1)}
    if iron_concentrate is not None:
        pct = (df[IRON] <= iron_concentrate).mean() * 100
        result["iron"] = {"value": iron_concentrate, "percentile": round(pct, 1),
                          "share_of_hours_with_higher_iron": round(100 - pct, 1)}

    # Levers: compare process variables in the best vs worst silica quartile
    best = df[df[SILICA] <= df[SILICA].quantile(.25)]
    worst = df[df[SILICA] >= df[SILICA].quantile(.75)]
    levers = []
    for col in df.columns.drop(["date", IRON, SILICA]):
        b, w = best[col].mean(), worst[col].mean()
        levers.append({"variable": col, "best_quartile_mean": round(b, 3),
                       "worst_quartile_mean": round(w, 3),
                       "difference_pct": round((b - w) / w * 100, 1) if w else None})
    levers.sort(key=lambda x: abs(x["difference_pct"] or 0), reverse=True)
    result["levers_best_vs_worst_silica_quartile"] = {
        "best_quartile_silica_max": round(df[SILICA].quantile(.25), 2),
        "worst_quartile_silica_min": round(df[SILICA].quantile(.75), 2),
        "top_differences": levers[:8],
        "caveat": "Correlation across hours, not proven cause and effect.",
    }
    return result


# == Tool registry for the OpenAI API ==
TOOLS = [  # Responses API format
    {
        "type": "function",
        "name": "get_brochure",
        "description": "Full text of one product brochure, with '## Page N' markers.",
        "parameters": {
            "type": "object",
            "properties": {"product": {"type": "string", "enum": list(list_brochures())}},
            "required": ["product"],
        },
    },
    {
        "type": "function",
        "name": "estimate_service_cost",
        "description": (
            "Cost, hours, rates and parts from historical field service reports for one equipment "
            "type. Pass country to also get the labour/travel rates seen in that country."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "equipment": {"type": "string", "enum": EQUIPMENT_NAMES},
                "country": {"type": "string", "description": "customer's country, e.g. Chile"},
            },
            "required": ["equipment"],
        },
    },
    {
        "type": "function",
        "name": "assess_flotation",
        "description": (
            "Compare a customer's iron ore flotation concentrate grades against hourly data from a reference "
            "iron ore flotation plant (percentiles; not the customer's own plant), and list process variables "
            "that differ most between the plant's best and worst silica hours."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "silica_concentrate": {"type": "number", "description": "% silica in concentrate"},
                "iron_concentrate": {"type": "number", "description": "% iron in concentrate"},
            },
        },
    },
]

FUNCTIONS = {
    "get_brochure": get_brochure,
    "estimate_service_cost": estimate_service_cost,
    "assess_flotation": assess_flotation,
}


def run_tool(name: str, arguments: str) -> str:
    if name not in FUNCTIONS:
        return json.dumps({"error": f"Unknown tool {name}"})
    try:
        return json.dumps(FUNCTIONS[name](**json.loads(arguments or "{}")), default=str)
    except Exception as e:  # report tool errors back to the model instead of crashing
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
