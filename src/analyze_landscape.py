"""
Phase 1 analysis: incretin pipeline landscape + efficacy-frontier teaser.

Reads:
    data/processed/trials.csv      (live ClinicalTrials.gov metadata)
    data/curated/drug_reference.csv
    data/curated/efficacy_draft.csv
Writes summary tables to data/processed/ and figures to figures/.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")
ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
PROC = ROOT / "data" / "processed"

trials = pd.read_csv(PROC / "trials.csv")
ref = pd.read_csv(ROOT / "data" / "curated" / "drug_reference.csv")
eff = pd.read_csv(ROOT / "data" / "curated" / "efficacy_draft.csv")

# --- generic-level attribute map (mechanism/status are consistent per generic) ---
gattr = (ref.sort_values("highest_status")
            .groupby("generic_name")
            .agg(mechanism_class=("mechanism_class", "first"),
                 n_targets=("n_targets", "max"),
                 sponsor=("sponsor", "first"),
                 is_marketed=("highest_status", lambda s: (s == "Marketed").any()))
            .reset_index())
t = trials.merge(gattr, left_on="matched_generic", right_on="generic_name", how="left")
t["cohort"] = t["is_marketed"].map({True: "Marketed", False: "Pipeline"})
t["start_year"] = pd.to_datetime(t["start_date"], errors="coerce").dt.year

PHASE_ORDER = ["EARLY_PHASE1", "PHASE1", "PHASE1|PHASE2", "PHASE2",
               "PHASE2|PHASE3", "PHASE3", "PHASE4", "NA"]


def save(name):
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  figure -> figures/{name}")


# 1. Trial volume per drug, split marketed vs pipeline
vol = (t.groupby(["matched_generic", "cohort"]).size()
         .reset_index(name="n").sort_values("n", ascending=True))
plt.figure(figsize=(9, 7))
pal = {"Marketed": "#4C72B0", "Pipeline": "#DD8452"}
for cohort, g in vol.groupby("cohort"):
    plt.barh(g["matched_generic"], g["n"], color=pal[cohort], label=cohort)
plt.xlabel("Registered trials (ClinicalTrials.gov)")
plt.title("Research intensity by drug: marketed vs pipeline incretins")
plt.legend()
save("01_trial_volume_by_drug.png")

# 2. Phase distribution among PIPELINE drugs only
pipe = t[t["cohort"] == "Pipeline"].copy()
pipe["phase"] = pd.Categorical(pipe["phase"], categories=PHASE_ORDER, ordered=True)
pc = pipe.groupby(["matched_generic", "phase"], observed=True).size().reset_index(name="n")
pivot = pc.pivot(index="matched_generic", columns="phase", values="n").fillna(0)
pivot = pivot.loc[pivot.sum(axis=1).sort_values().index]
pivot.plot(kind="barh", stacked=True, figsize=(9, 6), colormap="viridis")
plt.xlabel("Trials")
plt.title("Clinical-phase distribution of pipeline incretins")
plt.legend(title="Phase", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
save("02_pipeline_phase_distribution.png")

# 3. Mechanism-class landscape (drug-level, deduped to generics)
mech = (gattr.assign(cohort=gattr["is_marketed"].map({True: "Marketed", False: "Pipeline"}))
             .groupby(["mechanism_class", "cohort"]).size().reset_index(name="n"))
plt.figure(figsize=(9, 5))
sns.barplot(data=mech, y="mechanism_class", x="n", hue="cohort", palette=pal)
plt.xlabel("Number of distinct drugs")
plt.ylabel("")
plt.title("Mechanism-class evolution: where the pipeline is concentrating")
save("03_mechanism_class_landscape.png")

# 4. Pipeline trial momentum (trials started per year)
mo = (pipe.dropna(subset=["start_year"])
          .query("start_year >= 2018 and start_year <= 2026")
          .groupby("start_year").size())
plt.figure(figsize=(9, 5))
plt.plot(mo.index, mo.values, marker="o", color="#DD8452", linewidth=2)
plt.xlabel("Trial start year")
plt.ylabel("Pipeline trials started")
plt.title("Momentum: pipeline incretin trials launched per year")
save("04_pipeline_momentum.png")

# 5. Efficacy-frontier teaser: weight loss vs mechanism complexity
ef = eff.merge(ref[["drug_id", "n_targets", "route", "molecule_type"]], on="drug_id", how="left")
ef = ef.dropna(subset=["weight_loss_pct"])
plt.figure(figsize=(9, 6))
markers = {"oral": "s", "subcutaneous": "o"}
for route, g in ef.groupby("route"):
    plt.scatter(g["n_targets"], g["weight_loss_pct"], s=140,
                marker=markers.get(route, "o"), label=route, alpha=0.8)
    for _, r in g.iterrows():
        plt.annotate(r["generic_name"], (r["n_targets"], r["weight_loss_pct"]),
                     fontsize=7, xytext=(5, 4), textcoords="offset points")
plt.xticks([1, 2, 3], ["mono", "dual", "triple"])
plt.xlabel("Receptor targets (mechanism complexity)")
plt.ylabel("Peak weight loss (%)  [DRAFT - verify]")
plt.title("Efficacy frontier teaser: more targets -> more weight loss?")
plt.legend(title="Route")
save("05_efficacy_frontier_teaser.png")

# --- summary tables ---
summary = (t.groupby(["matched_generic", "cohort", "mechanism_class"])
             .agg(trials=("nct_id", "nunique"),
                  median_enrollment=("enrollment", "median"))
             .reset_index().sort_values("trials", ascending=False))
summary.to_csv(PROC / "drug_summary.csv", index=False)

print("\n=== Pipeline landscape summary ===")
print(f"Total unique trials: {t['nct_id'].nunique()}")
print(f"Marketed-drug trials: {(t['cohort']=='Marketed').sum()}  |  "
      f"Pipeline trials: {(t['cohort']=='Pipeline').sum()}")
print("\nTop sponsors by trial count:")
print(t["lead_sponsor"].value_counts().head(8).to_string())
print("\nPipeline drugs by highest active phase:")
print(pipe.groupby("matched_generic")["phase"].apply(
    lambda s: sorted(set(s.dropna()), reverse=True)[0] if len(s.dropna()) else "NA").to_string())
print(f"\n  table -> data/processed/drug_summary.csv")
