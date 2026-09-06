"""
Phase 2: what the efficacy frontier costs, and what the public record can answer.

Two figures:
  06  Evidence asymmetry -- weight loss vs the share of a drug's late-phase
      trials that have posted results. The frontier drugs are the ones with the
      least public safety data.
  07  Placebo-adjusted GI burden vs weight loss, for the trials that do report.

Figure 06 carries a confound that must travel with it: results posting is due 12
months after primary completion, so a 2026 candidate cannot have posted what a
2014 drug has. The defensible reading is availability -- a clinician cannot
evaluate these drugs from the public record today -- not concealment.

Placebo adjustment matters: trial populations differ, and background nausea runs
1% (AWARD-11) to 10% (SURMOUNT-1). Subtracting the concurrent control arm gives
the drug-attributable rate, which travels across trials far better than the raw
rate. It is still not a head-to-head -- durations and dose-escalation schedules
differ -- so this is a landscape, on the same terms as figure 05.
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC, CUR, FIG = ROOT / "data" / "processed", ROOT / "data" / "curated", ROOT / "figures"

eff = pd.read_csv(CUR / "efficacy.csv")
ref = pd.read_csv(CUR / "drug_reference.csv")
piv = pd.read_csv(CUR / "pivotal_trials.csv")
ae = pd.read_csv(PROC / "adverse_events.csv")
cov = pd.read_csv(PROC / "evidence_coverage.csv")


def save(name):
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  figure -> figures/{name}")


def is_placebo(title):
    return "placebo" in str(title).lower()


def dose_mg(title):
    m = re.search(r"(\d+(?:\.\d+)?)\s*mg", str(title), re.I)
    return float(m.group(1)) if m else -1.0


# ---- drug-attributable GI rates: top active dose minus concurrent control ----
rows = []
for (nct, drug_id), g in ae.groupby(["nct_id", "drug_id"]):
    arms = g[["arm_id", "arm_title"]].drop_duplicates()
    pbo = arms[arms.arm_title.map(is_placebo)]
    act = arms[~arms.arm_title.map(is_placebo)].copy()
    if pbo.empty or act.empty:
        continue
    # the drug's own top dose, not another drug's arm in the same trial
    gen = ref.loc[ref.drug_id == drug_id, "generic_name"]
    stem = str(gen.iloc[0])[:6].lower() if len(gen) else ""
    mine = act[act.arm_title.str.lower().str.contains(stem, na=False)] if stem else act
    act = mine if not mine.empty else act
    top = act.loc[act.arm_title.map(dose_mg).idxmax()]
    for term in ("nausea", "vomiting", "diarrhoea"):
        a = g[(g.arm_id == top.arm_id) & (g.term == term)]
        p = g[(g.arm_id.isin(pbo.arm_id)) & (g.term == term)]
        if a.empty:
            continue
        raw = float(a.pct.iloc[0])
        base = float(p.pct.mean()) if not p.empty else 0.0
        rows.append({"drug_id": drug_id, "nct_id": nct, "term": term,
                     "arm": top.arm_title, "control": "; ".join(pbo.arm_title),
                     "pct_active": raw, "pct_control": round(base, 2),
                     "pct_attributable": round(raw - base, 2)})
tol = pd.DataFrame(rows)
tol.to_csv(PROC / "tolerability_adjusted.csv", index=False)
print(f"  table -> data/processed/tolerability_adjusted.csv ({len(tol)} rows)")
print("\n  top-dose arm selected per trial:")
for _, r in tol[tol.term == "nausea"].iterrows():
    print(f"    {r.drug_id:<20} {r.arm[:34]:<34} nausea {r.pct_active:5.1f}% "
          f"- ctrl {r.pct_control:5.1f}% = {r.pct_attributable:5.1f}pp")

# ---- figure 06: evidence asymmetry ----
e = eff.dropna(subset=["weight_loss_pct"]).merge(
    ref[["drug_id", "generic_name", "route"]], on="drug_id", suffixes=("", "_r"))
e = e.merge(cov, left_on="generic_name_r", right_on="generic_name", how="left")
e = e.merge(piv[["drug_id", "results_posted"]], on="drug_id", how="left")
e = e.dropna(subset=["pct_late_phase_with_results"]).drop_duplicates("drug_id")

fig, ax = plt.subplots(figsize=(10, 6.5))
for posted, sub in e.groupby(e.results_posted.fillna("no")):
    ax.scatter(sub.pct_late_phase_with_results, sub.weight_loss_pct, s=170, alpha=.85,
               color="#4C72B0" if posted == "yes" else "#C44E52",
               marker="o" if posted == "yes" else "X",
               label="Pivotal trial has posted results" if posted == "yes"
                     else "Pivotal trial: no posted results",
               zorder=3, edgecolors="white", linewidth=1.2)
for _, r in e.iterrows():
    ax.annotate(r.generic_name_r, (r.pct_late_phase_with_results, r.weight_loss_pct),
                fontsize=7.5, xytext=(6, 4), textcoords="offset points")
ax.set_xlabel("Share of the drug's late-phase trials with results posted to ClinicalTrials.gov (%)")
ax.set_ylabel("Peak weight loss reported (%)")
ax.set_title("Evidence asymmetry: the biggest efficacy claims rest on the least public data")
ax.set_ylim(top=e.weight_loss_pct.max() + 1.6)
ax.grid(alpha=.3)
ax.legend(loc="upper right", fontsize=8)
plt.figtext(0.5, -0.05,
            "Efficacy from top-dose obesity readouts (see efficacy.csv); timepoints and estimands differ.\n"
            "CONFOUNDED BY AGE: posting is due 12 months after completion, so newer drugs mechanically have less. "
            "The claim is that these drugs cannot yet be evaluated from public data -- not that data is withheld.",
            ha="center", fontsize=7, style="italic", wrap=True)
save("06_evidence_asymmetry.png")

# ---- figure 07: drug-attributable GI burden vs efficacy ----
n = tol[tol.term == "nausea"].merge(
    eff[["drug_id", "generic_name", "weight_loss_pct", "a1c_reduction_pct"]], on="drug_id")
n = n.dropna(subset=["weight_loss_pct"])
fig, ax = plt.subplots(figsize=(10, 6.5))
ax.scatter(n.pct_attributable, n.weight_loss_pct, s=170, color="#4C72B0",
           zorder=3, edgecolors="white", linewidth=1.2)
for _, r in n.iterrows():
    ax.annotate(r.generic_name, (r.pct_attributable, r.weight_loss_pct),
                fontsize=8, xytext=(6, 4), textcoords="offset points")
missing = piv[piv.results_posted != "yes"].merge(
    eff[["drug_id", "generic_name", "weight_loss_pct"]], on="drug_id").dropna(subset=["weight_loss_pct"])
# Drugs with no public AE data are NOT zero-nausea drugs. Plotting them at x=0
# would read as "costs nothing", the opposite of "unknown", so they sit in a
# shaded band outside the measured scale, separated by a break line.
BAND = -9.0
lo = min(0.0, n.pct_attributable.min()) - 16
hi = n.pct_attributable.max() + 9
if not missing.empty:
    ax.axvspan(lo, -3.5, color="#C44E52", alpha=.07, zorder=0)
    ax.axvline(-3.5, color="#C44E52", ls=":", lw=1.2, alpha=.7, zorder=1)
    ax.scatter([BAND] * len(missing), missing.weight_loss_pct, s=150, marker="X",
               color="#C44E52", zorder=3, edgecolors="white", linewidth=1.0,
               label="no public AE data (value unknown)")
    for _, r in missing.iterrows():
        ax.annotate(r.generic_name, (BAND, r.weight_loss_pct), fontsize=7.5,
                    xytext=(7, 3), textcoords="offset points", color="#B0413E")
    ax.text(BAND, ax.get_ylim()[0], "no public data", fontsize=7.5, style="italic",
            color="#B0413E", ha="center", va="bottom")
    ax.legend(loc="lower right", fontsize=8)
ax.set_xlim(lo, hi)
# no numeric ticks inside the "unknown" band -- a -10 label implies a real value
ax.set_xticks([t for t in ax.get_xticks() if t >= 0])
ax.set_xlabel("Drug-attributable nausea (top dose minus concurrent control, percentage points)")
ax.set_ylabel("Peak weight loss (%)")
ax.set_title("What the frontier costs: nausea burden vs weight loss")
ax.grid(alpha=.3)
plt.figtext(0.5, -0.05,
            "Placebo-adjusted using each trial's own control arm. Not a head-to-head: trial duration, population and "
            "escalation schedules differ. Drugs in the shaded band have no public AE data -- unknown, not zero. "
            "Active-comparator trials (SURPASS-2, AWARD-11) have no placebo arm and cannot be adjusted this way.",
            ha="center", fontsize=7, style="italic", wrap=True)
save("07_gi_burden_vs_efficacy.png")

print("\n=== Evidence coverage, late-phase trials ===")
print(cov[["generic_name", "late_phase_trials", "late_phase_with_results",
           "pct_late_phase_with_results"]].to_string(index=False))
