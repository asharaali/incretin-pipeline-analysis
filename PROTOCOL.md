# Study protocol (draft v0.1)

**Public availability of results for obesity pharmacotherapy trials: a cross-sectional
analysis of ClinicalTrials.gov**

Ashar Ali · NJIT · drafted 2026-09-07 · **not yet reviewed by a faculty mentor**

> This protocol is written *before* the analysis is run, and the cohort is defined here
> rather than derived from what an earlier exploratory pass happened to show. That earlier
> pass (this repository's figure 06) is treated as hypothesis-generating only, and its
> numbers are deliberately not carried into this document as expectations.

---

## 1. Background

Sponsors of applicable clinical trials must post summary results to ClinicalTrials.gov
within 12 months of primary completion (FDAAA 801; 42 CFR Part 11). Compliance has been
studied across medicine broadly, but not for obesity pharmacotherapy specifically, a class
that has moved from marginal to among the most commercially significant in the industry
within roughly five years, and in which a large share of public efficacy claims currently
originate from sponsor press releases and conference abstracts rather than posted results
or peer-reviewed publication.

Clinicians and formulary committees are being asked to form views on these agents now.
Whether the underlying safety data is publicly available is therefore a practical question,
not only a policy one.

## 2. Objectives

**Primary.** Among trials of obesity pharmacotherapy with a results-reporting obligation
under FDAAA 801, what proportion posted results within 12 months of primary completion?

**Secondary.**
1. Does timely posting differ between agents already marketed at the time of primary
   completion and agents still investigational at that time?
2. Does it differ by sponsor class (industry / academic / other)?
3. Among trials with no posted results, what is the median time elapsed past the deadline?

## 3. Design

Cross-sectional analysis of a public trial registry. No human subjects contact, no private
data. Expected to qualify as non-human-subjects research and therefore IRB-exempt;
**confirm with NJIT IRB before submission rather than asserting it.**

## 4. Data source

ClinicalTrials.gov API v2. Retrieved programmatically; the fetch code and a dated raw
snapshot are archived in this repository so the extraction is reproducible.

**Census date: to be fixed at extraction and stated in the manuscript.** All
deadline arithmetic is relative to the census date.

## 5. Cohort

**Inclusion**
- Interventional study
- At least one intervention is a pharmacologic agent for weight management or obesity
- Phase 2, 2/3, 3 or 4
- Primary completion date on or before (census date − 12 months)

**Exclusion**
- Observational or expanded-access records
- Withdrawn trials (no participants enrolled)
- Trials whose only obesity link is a comorbidity eligibility criterion rather than a
  weight-related endpoint

**Drug set.** The 14-drug incretin set already curated in `data/curated/drug_reference.csv`
is the starting frame. **Open question for mentor:** whether to widen to all obesity
pharmacotherapy (adding orlistat, phentermine/topiramate, naltrexone/bupropion, setmelanotide)
which strengthens generalisability, or to hold to the incretin class which keeps the
comparison mechanistically tight. Widening is probably the stronger paper.

## 6. Exposure variable

Marketing status of the agent **at the trial's primary completion date**, not at the census
date. Determined from regulatory sources (FDA approval letters, NMPA announcements), not
from registry phase labels.

> Registry `PHASE4` labels are **not** approval status. Investigator-initiated Phase 4
> records exist for unapproved agents; this was verified in the exploratory pass and is a
> known trap.

## 7. Primary outcome

Binary: results posted to ClinicalTrials.gov on or before (primary completion date +
12 months), from `resultsFirstPostDate` (or `resultsFirstSubmitDate`, with the choice
prespecified and stated).

## 8. FDAAA applicability determination

**This is the methodological core and the most likely point of failure.** Counting trials
that carried no legal obligation would make the headline proportion meaningless.

Applicability will be determined per trial against the statutory criteria: interventional
study of an FDA-regulated drug or biologic; phase 2 or later; at least one study site in the
United States; and initiated after 27 Sep 2007 or ongoing as of 26 Dec 2007. Trials of
agents never under FDA jurisdiction (for example, agents developed and trialled solely in
China) are outside the requirement and will be reported separately rather than counted as
non-compliant.

Registry records do not expose an applicability flag, so the determination is derived and
therefore fallible. Planned mitigations:
- Publish the determination algorithm and the per-trial classification as supplementary data
- Report the primary outcome both across all included trials and restricted to the
  high-confidence applicable subset
- Have a second reader independently classify a random sample and report agreement

**This is the specific point on which mentor input is most needed.**

## 9. Analysis

Descriptive proportions with 95% confidence intervals. Group comparisons by chi-square or
Fisher's exact as cell counts require. Time past deadline summarised as median with IQR.
Analysis in Python (pandas); code committed to this repository.

No imputation. Trials with missing primary completion dates are excluded and counted in the
flow diagram.

## 10. Limitations (stated up front, not discovered later)

- **Posting is not the same as availability.** A trial may be published in a journal without
  posted registry results. The primary outcome measures registry compliance specifically;
  a secondary check of PubMed linkage would strengthen the claim about true availability and
  should probably be added.
- **Recency confounding.** Newer agents have had less calendar time to accumulate posted
  results. This is handled by anchoring every trial to its own deadline rather than to the
  census date, but residual confounding by drug age remains and must be stated.
- **The claim is availability, not concealment.** Nothing in this design can distinguish a
  sponsor withholding data from a sponsor within an administrative lag.

## 11. Open questions for a mentor

1. Is the FDAAA applicability derivation defensible, or does it need a narrower cohort where
   applicability is unambiguous?
2. Widen to all obesity pharmacotherapy, or hold to incretins?
3. `resultsFirstPostDate` vs `resultsFirstSubmitDate` as the primary field?
4. Is a PubMed-linkage secondary analysis worth the added scope?
5. Realistic target journal: JMCP, JAPhA, Annals of Pharmacotherapy, BMJ Open?

## 12. Prior work to check before proceeding

- FDAAA compliance literature (Goldacre et al. and the FDAAA TrialsTracker) for method
  precedent and to avoid reinventing the applicability algorithm
- Dovepress DMSO, May 2026: analysis of 227 completed GLP-1 obesity trials. **Read in full
  before committing.** It appears to treat reporting gaps as a limitation rather than as an
  outcome, but if it measured posting directly, this study needs to change or narrow.
