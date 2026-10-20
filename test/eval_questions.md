# Eval questions

Each question is run in a fresh conversation by `run_demo.py`. Transcripts go to `demo_transcripts.md`.

## 1. Spec lookup (answer in one brochure)
**Q:** What flow range and inlet sizes do the MD series mill discharge pumps cover?

**Expected:** Calls `get_brochure(md-series-pump)`. Flows up to 12000 m3/h, inlet sizes 250–700 mm, metal or rubber lining. Cites [md-series-pump, page 1].

## 2. Spec not in the brochures
**Q:** What is the installed motor power in kW of a Concorde Cell?

**Expected:** Calls `get_brochure(concorde-cell)`. Says the brochure does not state motor power. Does not give a number for it.

## 3. Recommendation
**Q:** Customer has fine particles and wants better concentrate grade in the cleaner circuit — what do we offer?

**Expected:** Reads the relevant flotation brochures. Recommends one specific product (Concorde Cell and/or ColumnCell), ties it to "fine particles" and "cleaner/grade", quotes the supporting brochure facts with page citations.

## 4. Vague recommendation → clarify
**Q:** My customer wants to improve their plant. What should we offer them?

**Expected:** Asks one clarifying question (e.g. which process area or problem). No product recommendation, no numbers.

## 5. Product without a brochure
**Q:** Do we have a brochure for the SALA VSP-750 sump pump?

**Expected:** Says there is no brochure for it. May mention it appears in service history. States no specs for it.

## 6. Purchase price (not in data)
**Q:** What does a Larox PF-DS cost to buy?

**Expected:** Says purchase prices are not in the data. Does not invent a price. May offer service-cost history instead, without presenting it as a purchase price.

## 7. Cost estimate: Concorde Cell maintenance
**Q:** What does a typical Concorde Cell maintenance visit cost?

**Expected:** Calls `estimate_service_cost(Concorde Cell)`. Gives ranges per currency (not converted), number of reports and FSR IDs, notes how many reports have no cost, flags low confidence.

## 8. Cost estimate: Orion pump seal replacement
**Q:** Roughly what would a seal replacement on an Orion slurry pump cost?

**Expected:** Calls `estimate_service_cost(Orion series horizontal slurry pump)`. Uses reports where a seal was replaced (FSR-0003 has a cost; FSR-0038 has none). States low confidence, gives FSR IDs and currency. Does not present costs of unrelated jobs as seal-replacement costs.

## 9. Cost estimate: no service history
**Q:** Can you estimate the service cost for a FloatForce upgrade?

**Expected:** Calls `estimate_service_cost(FloatForce upgrade)`, gets no reports. Says there is no service history, gives no number.

## 10. Flotation assessment
**Q:** The customer is getting 3.1% silica and 64.5% iron in their concentrate. They think that's normal. What do you think, and what could we suggest?

**Expected:** Calls `assess_flotation(3.1, 64.5)`. Silica ~76th percentile (worse than typical), iron ~28th percentile. Levers from computed differences, labelled as correlations. If a product is suggested, calls `get_brochure` and cites it.
