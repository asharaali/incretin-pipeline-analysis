# Incretin Pipeline & Comparative-Efficacy Analysis

A reproducible data-analytics study of the weight-loss / glycemic-control drug class — comparing
marketed incretin therapies (Ozempic, Wegovy, Rybelsus, Mounjaro, Zepbound, and others) against the
early-, mid-, and late-phase clinical pipeline behind them.

**Author:** Ashar Ali — NJIT (Biology, pre-pharmacy) · 1,000+ pharmacy intern hours

---

## Thesis

The incretin field is moving along three measurable axes:

1. **Mechanism complexity is rising** — from single GLP-1 agonists → dual (GLP-1/GIP, GLP-1/glucagon)
   → triple (GLP-1/GIP/glucagon) agonists, with amylin combinations emerging.
2. **Efficacy scales with mechanism complexity** — peak weight loss climbs from ~8–15% (mono) to
   ~19–23% (dual) to ~24% (triple).
3. **The route of administration has already shifted.** Orforglipron, an oral small molecule, was
   **FDA-approved 1 Apr 2026 (Foundayo)** — the first GLP-1 pill for weight loss without food or
   water timing restrictions. Oral-peptide candidates (amycretin, oral VK2735) are behind it.
   *This project's v1, written June 2026, still filed orforglipron as pipeline: the approval was
   already ~12 weeks old and the analysis had not caught it. That is the case for refreshing a
   live-data project on a schedule rather than treating a snapshot as done.*

This project quantifies all three using live regulatory data and curated pivotal-trial outcomes.

## Project phases

| Phase | Question | Status |
|-------|----------|--------|
| **1. Pipeline landscape** | Where is the field concentrating (phase, sponsor, mechanism, route)? | ✅ v2 |
| **2. Efficacy frontier** | How much better is each drug, at what tolerability cost — and can we even tell? | ✅ v1 |
| **3. Oral vs injectable** | Is the oral wave real, and how big is the efficacy gap? | 🔜 |

**Data refreshed 2026-09-05** (previous snapshot 2026-06-24): 1,730 trials, +108 net.
See *Trial attribution* below — this refresh also corrected two attribution defects that
materially changed per-drug counts.

## Trial attribution

One trial can name several drugs in this set — a head-to-head, a combination, or an active
comparator. Two rules decide who a trial belongs to, and both were bugs in v1:

**Search aliases.** A candidate may be registered only under a sponsor code. Amycretin appears
once under `amycretin` but 32 more times under `NNC0487-0111` / `NNC0519-0130`. `search_term` in
`drug_reference.csv` therefore holds `|`-separated aliases, all of which are queried.

**Most-specific term wins.** v1 kept whichever drug was fetched first, so every CagriSema trial was
swallowed by semaglutide and the combination drug had *zero* trials of its own. Attribution now goes
to the matching term with the smallest corpus — a stable proxy for specificity that does not depend
on row order. For a SURPASS-style head-to-head this credits the experimental arm, not the comparator.
Every trial carries `attributed_term` and an `ambiguous` flag (176 trials match >1 drug) so the call
is auditable and reversible.

Effect of the two fixes on the June counts:

| Drug | Jun 2026 | Sep 2026 | Δ |
|---|---:|---:|---:|
| semaglutide | 706 | 602 | −104 |
| tirzepatide | 188 | 251 | +63 |
| amycretin | 1 | 33 | +32 |
| cagrilintide+semaglutide | **0** | 30 | +30 |
| dulaglutide | 102 | 132 | +30 |

## Status changes since June 2026

| Drug | Was | Now | Evidence |
|---|---|---|---|
| orforglipron | Phase 3 | **Marketed** | FDA approval 2026-04-01 (Foundayo) |
| mazdutide | Phase 3 | **Marketed (China)** | NMPA 2025-06 obesity, 2025-09 T2D |
| amycretin | Phase 2 | **Phase 3** | AMAZE 1–12 program, first posted 2026-02 |
| VK2735 | Phase 2 | **Phase 3** | VANQUISH-1/2, started 2025-06 |
| pemvidutide | Phase 2 | **Phase 3** | NCT07795164, started 2026-07 |

Registry phase labels are **not** approval status — investigator-initiated `PHASE4` records exist for
unapproved drugs. Every status change above was confirmed against a regulatory or sponsor source and
carries `status_asof` + `status_source` columns in `drug_reference.csv`.

## Phase 2 findings

**Tirzepatide dominates semaglutide on both axes.** At top dose it produces more weight loss
(20.9% vs 14.9%) *and* less drug-attributable nausea (22.1 vs 35.4 percentage points over each
trial's own control arm). That is not the trade-off the mechanism-complexity story predicts, and
it is visible only once nausea is placebo-adjusted.

**Survodutide is the tolerability outlier** — 49.5 pp attributable nausea for 14.9% weight loss,
the worst ratio in the set. **Liraglutide is dominated by everything**: least weight loss (8.0%),
32.6 pp nausea.

**Half the frontier cannot be evaluated at all.** CagriSema, amycretin, VK2735, pemvidutide,
ecnoglutide and mazdutide have **no adverse-event data in the public registry** — zero posted
results across 76 late-phase trials between them. Their efficacy numbers come from press releases
and conference abstracts. The drugs with the loudest efficacy claims are the ones a clinician
currently has the least ability to assess.

⚠️ **That last finding is confounded by age and the README will not overstate it.** Results posting
is due 12 months after primary completion, so a candidate that entered Phase 3 in 2026 *cannot*
have posted what a drug approved in 2014 has. The supportable claim is about **availability** —
these drugs cannot yet be judged on public evidence — not about concealment.

### Method notes that matter

- **Placebo-adjusted, not raw.** Background nausea ranges from 1% (AWARD-11) to 10% (SURMOUNT-1)
  across these populations, so raw rates are not comparable. Each drug is adjusted against its own
  trial's concurrent control.
- **Active-comparator trials cannot be adjusted this way.** SURPASS-2 and AWARD-11 have no placebo
  arm, so tirzepatide's T2D row and dulaglutide are absent from figure 07 by design.
- **Study withdrawal ≠ drug discontinuation.** The registry's participant-flow "Adverse Event"
  dropout counts leaving the *study*. For tirzepatide 15 mg that is 3.5%; the publication's
  drug-discontinuation figure is ~7%. Both are emitted under names that keep them apart, and
  arm-mapping is refused outright when a trial's flow and event groups don't align (SCALE Obesity).
- **Unknown is not zero.** Drugs without public AE data sit in a shaded off-scale band in figure 07
  rather than at x=0, which would read as "costs nothing".

## Data sources

- **Trial metadata** — [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api),
  pulled live and programmatically (phase, status, sponsor, enrollment, dates). Fully reproducible.
- **Efficacy outcomes** — hand-curated from pivotal-trial publications (STEP, SURMOUNT, SURPASS,
  SUSTAIN, PIONEER, REDEFINE, and named phase 2/3 readouts). See the data caveat below.
- **Adverse events** — pulled programmatically from the ClinicalTrials.gov **results database**,
  where sponsors post per-arm counts under a shared MedDRA vocabulary. Deliberately *not*
  hand-curated: this keeps the tolerability layer regenerable and consistently defined, and makes
  the coverage gap measurable instead of invisible.

## Reproduce

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/fetch_clinicaltrials.py     # pull live trial metadata
python src/fetch_adverse_events.py     # pull posted adverse-event results
python src/analyze_landscape.py        # Phase 1 tables + figures
python src/analyze_tolerability.py     # Phase 2 tables + figures
```

## Repository layout

```
data/
  curated/   drug_reference.csv     drug master: mechanism, route, molecule type, status,
                                    search aliases, status provenance
             efficacy.csv           curated pivotal-trial outcomes w/ source + estimand
             pivotal_trials.csv     drug -> pivotal NCT id, with resolution notes
  processed/ trials.csv             flattened live trial metadata + attribution columns
             drug_summary.csv       per-drug rollup
             adverse_events.csv     per-arm, per-term GI event rates
             ae_arm_summary.csv     per-arm rollup + study-withdrawal rates
             evidence_coverage.csv  per-drug results-posting audit
             tolerability_adjusted.csv  placebo-adjusted GI rates at top dose
src/
  fetch_clinicaltrials.py           ClinicalTrials.gov API v2 client
  fetch_adverse_events.py           results-database client (adverse events)
  analyze_landscape.py              Phase 1 analysis + figures
  analyze_tolerability.py           Phase 2 analysis + figures
figures/                            generated charts
```

## ⚠️ Data caveat

Efficacy figures in `efficacy.csv` carry a `source`, `estimand`, `timepoint_wks`, and `verified` column.
Rows marked `web-verified-2026-06` were checked against the primary publication / sponsor release;
rows marked `needs-verify` still require confirmation. Because trials differ in **timepoint (13–72 wks)**,
**population**, and **estimand** (treatment-policy vs treatment-regimen vs efficacy/completer), the
efficacy-frontier figure is a **descriptive landscape, not a head-to-head comparison** — head-to-head
claims require matched estimands and direct or network meta-analysis. Trial metadata from
ClinicalTrials.gov is authoritative and regenerable.

## License

MIT (code). Curated data tables are for research/educational use; verify against primary sources.
