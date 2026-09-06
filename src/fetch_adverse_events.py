"""
Pull sponsor-reported adverse-event results for the pivotal trials.

Efficacy numbers in this project are hand-curated from publications; tolerability
is not. Adverse-event rates come from the ClinicalTrials.gov results database,
where sponsors post per-arm counts under a common MedDRA vocabulary. That makes
the tolerability layer regenerable and comparably defined across trials, instead
of being retyped out of PDFs and supplementary appendices.

Two limits are deliberate and are carried into the output rather than hidden:

  * Coverage is partial. Results are posted for the marketed drugs and for two
    pipeline readouts; the newest candidates have none. `evidence_coverage.csv`
    records that gap, because the gap is itself a finding.

  * The participant-flow "Adverse Event" dropout counts withdrawal from the
    STUDY, which is not the same as discontinuing STUDY DRUG -- the number
    publications usually report. For tirzepatide 15 mg in SURMOUNT-1 the two are
    1.0% and ~7%. Both are emitted, under names that keep them apart.

Usage:
    python src/fetch_adverse_events.py
Outputs:
    data/processed/adverse_events.csv     per-arm, per-term GI event rates
    data/processed/ae_arm_summary.csv     per-arm rollup + study-withdrawal rates
    data/processed/evidence_coverage.csv  per-drug results-posting audit
"""
import csv
import time
from pathlib import Path

import requests

API = "https://clinicaltrials.gov/api/v2/studies"
ROOT = Path(__file__).resolve().parents[1]
PIVOTAL = ROOT / "data" / "curated" / "pivotal_trials.csv"
TRIALS = ROOT / "data" / "processed" / "trials.csv"
PROC = ROOT / "data" / "processed"

# MedDRA preferred terms that make up the GI tolerability burden patients feel.
GI_TERMS = {
    "nausea", "vomiting", "diarrhoea", "diarrhea", "constipation",
    "abdominal pain", "abdominal pain upper", "dyspepsia", "eructation",
    "gastrooesophageal reflux disease", "abdominal distension", "flatulence",
}


def fetch_study(nct):
    r = requests.get(f"{API}/{nct}", timeout=90)
    r.raise_for_status()
    return r.json()


def arm_rows(nct, drug_id, trial, study):
    """Per-arm GI event rates plus a study-withdrawal rollup."""
    res = study.get("resultsSection") or {}
    ae = res.get("adverseEventsModule") or {}
    groups = {g["id"]: g for g in ae.get("eventGroups", [])}
    if not groups:
        return [], []

    events, summary = [], []
    for e in ae.get("otherEvents", []) + ae.get("seriousEvents", []):
        term = (e.get("term") or "").strip()
        if term.lower() not in GI_TERMS:
            continue
        for s in e.get("stats", []):
            at_risk = s.get("numAtRisk")
            affected = s.get("numAffected")
            if not at_risk or affected is None:
                continue
            events.append({
                "nct_id": nct, "drug_id": drug_id, "key_trial": trial,
                "arm_id": s["groupId"],
                "arm_title": groups.get(s["groupId"], {}).get("title", ""),
                "term": term.lower(),
                "n_affected": affected, "n_at_risk": at_risk,
                "pct": round(100 * affected / at_risk, 2),
            })

    # study withdrawal attributed to an adverse event (NOT drug discontinuation)
    flow = res.get("participantFlowModule") or {}
    fgroups = {g["id"]: g["title"] for g in flow.get("groups", [])}
    withdrew, started = {}, {}
    for per in flow.get("periods", []):
        for m in per.get("milestones", []):
            if m.get("type", "").upper() == "STARTED":
                for a in m.get("achievements", []):
                    try:
                        started.setdefault(a["groupId"], int(a["numSubjects"]))
                    except (TypeError, ValueError, KeyError):
                        pass
        for dw in per.get("dropWithdraws", []):
            if dw.get("type", "").strip().lower() != "adverse event":
                continue
            for a in dw.get("reasons", []):
                try:
                    withdrew[a["groupId"]] = withdrew.get(a["groupId"], 0) + int(a["numSubjects"])
                except (TypeError, ValueError):
                    pass

    # Flow groups and event groups are separate id spaces (FG000 / EG000) that
    # happen to be positionally aligned -- but only when the study defines the
    # same arms in both. Titles are not reliable keys ("Sema 2.4 mg" vs
    # "Semaglutide 2.4 mg"), so align by position and refuse to guess otherwise:
    # a wrong dropout number is worse than a blank one.
    aligned = len(fgroups) == len(groups)
    for gid, g in groups.items():
        at_risk = g.get("otherNumAtRisk") or g.get("seriousNumAtRisk")
        fid = gid.replace("EG", "FG") if aligned else None
        n_start = started.get(fid)
        wd = withdrew.get(fid)
        summary.append({
            "nct_id": nct, "drug_id": drug_id, "key_trial": trial,
            "arm_id": gid, "arm_title": g.get("title", ""),
            "n_at_risk": at_risk,
            "deaths": g.get("deathsNumAffected"),
            "serious_ae_n": g.get("seriousNumAffected"),
            "serious_ae_pct": round(100 * g["seriousNumAffected"] / g["seriousNumAtRisk"], 2)
                if g.get("seriousNumAffected") is not None and g.get("seriousNumAtRisk") else "",
            "study_withdrawal_ae_n": wd if wd is not None else "",
            "study_withdrawal_ae_pct": round(100 * wd / n_start, 2)
                if wd is not None and n_start else "",
            "arm_alignment": "positional" if aligned else "unmatched",
        })
    return events, summary


def coverage():
    """Per-drug audit: how much of each drug's trial base has posted results."""
    rows = []
    with open(TRIALS, newline="") as f:
        trials = list(csv.DictReader(f))
    by_drug = {}
    for t in trials:
        d = by_drug.setdefault(t["matched_generic"], {"n": 0, "res": 0, "late": 0, "late_res": 0})
        d["n"] += 1
        posted = t.get("has_results") == "yes"
        d["res"] += posted
        if t["phase"] in ("PHASE2", "PHASE2|PHASE3", "PHASE3", "PHASE4"):
            d["late"] += 1
            d["late_res"] += posted
    for drug, d in sorted(by_drug.items(), key=lambda kv: -kv[1]["n"]):
        rows.append({
            "generic_name": drug, "trials": d["n"], "trials_with_results": d["res"],
            "pct_with_results": round(100 * d["res"] / d["n"], 1) if d["n"] else 0,
            "late_phase_trials": d["late"], "late_phase_with_results": d["late_res"],
            "pct_late_phase_with_results": round(100 * d["late_res"] / d["late"], 1) if d["late"] else 0,
        })
    return rows


def write(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  table -> {path.relative_to(ROOT)}  ({len(rows)} rows)")


def main():
    with open(PIVOTAL, newline="") as f:
        pivotal = list(csv.DictReader(f))

    all_events, all_summary = [], []
    for p in pivotal:
        nct = p["nct_id"].strip()
        if not nct:
            print(f"  {p['drug_id']:<20} no NCT resolved -- {p['resolution_note']}")
            continue
        if p["results_posted"] != "yes":
            print(f"  {p['drug_id']:<20} {nct}  no results posted")
            continue
        study = fetch_study(nct)
        e, s = arm_rows(nct, p["drug_id"], p["key_trial"], study)
        all_events += e
        all_summary += s
        print(f"  {p['drug_id']:<20} {nct}  {len(s)} arms, {len(e)} GI event rows")
        time.sleep(0.34)

    write(PROC / "adverse_events.csv", all_events)
    write(PROC / "ae_arm_summary.csv", all_summary)
    write(PROC / "evidence_coverage.csv", coverage())

    have = {r["drug_id"] for r in all_summary}
    missing = [p["drug_id"] for p in pivotal if p["drug_id"] not in have]
    print(f"\n  tolerability data for {len(have)}/{len(pivotal)} pivotal trials")
    print(f"  no public AE data: {', '.join(missing)}")


if __name__ == "__main__":
    main()
