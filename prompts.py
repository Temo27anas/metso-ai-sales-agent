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
