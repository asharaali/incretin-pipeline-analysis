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
3. **The route of administration is shifting** — oral small-molecule and oral-peptide candidates
   (orforglipron, amycretin, oral VK2735) are challenging the injectable standard.

This project quantifies all three using live regulatory data and curated pivotal-trial outcomes.

## Project phases

| Phase | Question | Status |
|-------|----------|--------|
| **1. Pipeline landscape** | Where is the field concentrating (phase, sponsor, mechanism, route)? | ✅ v1 |
| **2. Efficacy frontier** | How much better is each drug, at what convenience cost? | 🔜 |
| **3. Oral vs injectable** | Is the oral wave real, and how big is the efficacy gap? | 🔜 |

## Data sources

- **Trial metadata** — [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api),
  pulled live and programmatically (phase, status, sponsor, enrollment, dates). Fully reproducible.
- **Efficacy outcomes** — hand-curated from pivotal-trial publications (STEP, SURMOUNT, SURPASS,
  SUSTAIN, PIONEER, REDEFINE, and named phase 2/3 readouts). See the data caveat below.

## Reproduce

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/fetch_clinicaltrials.py     # pull live trial metadata
python src/analyze_landscape.py        # generate tables + figures
```

## Repository layout

```
data/
  curated/   drug_reference.csv     drug master: mechanism, route, molecule type, status
             efficacy_draft.csv     curated pivotal-trial outcomes (DRAFT — see caveat)
  processed/ trials.csv             flattened live trial metadata
             drug_summary.csv       per-drug rollup
src/
  fetch_clinicaltrials.py           ClinicalTrials.gov API v2 client
  analyze_landscape.py              Phase 1 analysis + figures
figures/                            generated charts
```

## ⚠️ Data caveat

Efficacy figures in `efficacy_draft.csv` are flagged `VERIFY` and are **not yet citation-grade**.
Every number must be confirmed against the primary publication (with dose, population, timepoint, and
whether the value is total or placebo-adjusted) before any external use or manuscript submission.
Trial metadata from ClinicalTrials.gov is authoritative and regenerable.

## License

MIT (code). Curated data tables are for research/educational use; verify against primary sources.
