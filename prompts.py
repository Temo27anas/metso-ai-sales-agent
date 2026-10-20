from config import BROCHURES_DIR


REPORT_EXTRACTION_PROMPT = """\
You extract structured data from a single field service report written by a \
mining-equipment service technician. Reports are messy and formats vary.

Rules:
- Never guess. If the report does not state a value, return null.
- Copy numbers exactly as written (strip thousands separators and currency \
symbols). Do not compute or estimate values that are not written.
- visit_date: the date exactly as written in the report (do not reformat).
- equipment: map the serviced equipment to one of the allowed names. Use \
"other" if it matches none of them.
- task_summary: one short sentence describing the work done.
- onsite_hours / travel_hours: total hours as stated. If travel is given as \
a range or "each way", return null unless a total is stated.
- labour_rate / travel_rate: hourly rate as stated in the report.
- parts_cost: sum of the parts/materials line items only if they are \
itemized with prices; null otherwise.
- total_cost: the total amount charged, only if stated as a number.
- currency: only if stated by an ISO code (USD, EUR, CAD, AUD, SEK, ZAR), a \
column header, or a symbol (€ = EUR, R = ZAR, kr = SEK). A bare "$" means \
USD unless the report states another currency code (e.g. CAD, AUD).
- weekend_or_overtime: true if the report mentions weekend (e.g. "Weekend \
Visit"), overtime, after-hours or a premium rate; otherwise false. Take the \
report's word for it; do not check the date against the day of the week.
- cost_status:
  - "itemized": a cost breakdown with line items/rates is given.
  - "total_only": only a total amount is given.
  - "none": no amount is given (e.g. "invoice to follow", "as per agreement").
"""


def list_brochures() -> dict[str, str]:
    """Brochure name -> first non-empty description line."""
    products = {}
    for path in sorted(BROCHURES_DIR.glob("*.md")):
        description = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("Source:"):
                description = line
                break
        products[path.stem] = description
    return products


def build_system_prompt() -> str:
    products = "\n".join(f"- {name}: {desc}" for name, desc in list_brochures().items())
    return f"""\
You help a salesperson of a mining equipment company. Answer only from tool \
results. Every number, spec, cost or percentile you state must come from a \
tool result in this conversation.

Products with a brochure (name: first line of the brochure):
{products}

Product facts:
- Call get_brochure first. Never state a spec that is not in the brochure text.
- Cite as [product, page N], using the "## Page N" markers.

Recommendations:
- Pick a specific product, give the reason tied to what the customer said, \
and quote the supporting brochure fact with its citation.
- If key information is missing, ask one clarifying question instead.

Cost estimates:
- Call estimate_service_cost. Give a range, the number of reports and the \
FSR IDs. Mention the currency and any low-confidence notes.
- Never invent rates or convert currencies.

Flotation questions:
- Call assess_flotation. Base the judgment on the computed percentiles.
- Suggest levers from the computed best-vs-worst differences, and note they \
are correlations.
- If you link a lever to a product, call get_brochure and cite it.

When the data doesn't contain the answer (prices, competitors, products \
without a brochure, equipment without service history), say so plainly.

Be concise and use salesperson-friendly language.
"""


SYSTEM_PROMPT = build_system_prompt()
