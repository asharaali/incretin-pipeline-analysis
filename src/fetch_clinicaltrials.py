"""
Fetch live trial metadata for the incretin drug set from the ClinicalTrials.gov API v2.

Source of truth for trial metadata (phase, status, sponsor, enrollment, dates).
Efficacy numbers are NOT here -- they live in data/curated/efficacy_draft.csv,
hand-curated from primary publications.

Usage:
    python src/fetch_clinicaltrials.py
Outputs:
    data/raw/trials_raw.json      full API records (audit trail)
    data/processed/trials.csv     one row per trial, flattened
"""
import csv
import json
import time
from pathlib import Path

import requests

API = "https://clinicaltrials.gov/api/v2/studies"
ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "curated" / "drug_reference.csv"
RAW_OUT = ROOT / "data" / "raw" / "trials_raw.json"
CSV_OUT = ROOT / "data" / "processed" / "trials.csv"

FIELDS = ",".join([
    "NCTId", "BriefTitle", "Phase", "OverallStatus", "StudyType",
    "Condition", "InterventionName", "LeadSponsorName", "LeadSponsorClass",
    "EnrollmentCount", "StartDate", "PrimaryCompletionDate", "HasResults",
])


def search_terms():
    """Unique drug search terms from the reference table.

    A drug's `search_term` cell may hold several "|"-separated aliases. Some
    candidates are registered on ClinicalTrials.gov only under a sponsor code
    (amycretin -> NNC0487-0111 / NNC0519-0130), so searching the generic name
    alone undercounts them badly.
    """
    terms = {}
    with open(REF, newline="") as f:
        for row in csv.DictReader(f):
            for alias in row["search_term"].split("|"):
                alias = alias.strip()
                if alias:
                    terms.setdefault(alias, row["generic_name"])
    return terms


def fetch_term(term):
    """Page through all studies whose intervention matches `term`."""
    studies, token = [], None
    while True:
        params = {
            "query.intr": term,
            "fields": FIELDS,
            "pageSize": 1000,
            "format": "json",
        }
        if token:
            params["pageToken"] = token
        r = requests.get(API, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        studies.extend(data.get("studies", []))
        token = data.get("nextPageToken")
        if not token:
            break
        time.sleep(0.34)  # be polite to the API
    return studies


def get(d, *path, default=None):
    for key in path:
        if isinstance(d, dict):
            d = d.get(key)
        else:
            return default
    return d if d is not None else default


def flatten(study, matched_term, matched_generic):
    p = study.get("protocolSection", {})
    phases = get(p, "designModule", "phases", default=[]) or []
    interventions = get(p, "armsInterventionsModule", "interventions", default=[]) or []
    return {
        "nct_id": get(p, "identificationModule", "nctId", default=""),
        "title": get(p, "identificationModule", "briefTitle", default=""),
        "phase": "|".join(phases) if phases else "NA",
        "status": get(p, "statusModule", "overallStatus", default=""),
        "study_type": get(p, "designModule", "studyType", default=""),
        "enrollment": get(p, "designModule", "enrollmentInfo", "count", default=""),
        "lead_sponsor": get(p, "sponsorCollaboratorsModule", "leadSponsor", "name", default=""),
        "sponsor_class": get(p, "sponsorCollaboratorsModule", "leadSponsor", "class", default=""),
        "conditions": "|".join(get(p, "conditionsModule", "conditions", default=[]) or []),
        "interventions": "|".join(i.get("name", "") for i in interventions),
        "has_results": "yes" if study.get("hasResults") else "no",
        "start_date": get(p, "statusModule", "startDateStruct", "date", default=""),
        "primary_completion": get(p, "statusModule", "primaryCompletionDateStruct", "date", default=""),
        "matched_term": matched_term,
        "matched_generic": matched_generic,
        "attributed_term": matched_term,
        "ambiguous": "no",
    }


def main():
    terms = search_terms()
    raw, seen, hits, corpus = [], {}, {}, {}
    for term, generic in terms.items():
        print(f"  fetching {term} ...", end="", flush=True)
        studies = fetch_term(term)
        print(f" {len(studies)} studies")
        corpus[term] = len(studies)
        for s in studies:
            raw.append(s)
            row = flatten(s, term, generic)
            nct = row["nct_id"]
            if not nct:
                continue
            seen.setdefault(nct, row)
            hits.setdefault(nct, []).append(term)

    # Attribution: a trial matching several drug terms belongs to the most
    # SPECIFIC one -- the term with the smallest corpus. Without this, a
    # CagriSema trial (which names semaglutide as a component) is swallowed by
    # the semaglutide corpus and the combination drug disappears entirely.
    # Corpus size is a stable proxy for specificity and, unlike first-seen-wins,
    # does not depend on the order rows happen to sit in the reference table.
    rows = []
    for nct, row in seen.items():
        matched = sorted(hits[nct], key=lambda x: (corpus[x], x))
        best = matched[0]
        row["matched_term"] = ";".join(matched)
        row["matched_generic"] = terms[best]
        row["attributed_term"] = best
        row["ambiguous"] = "yes" if len(matched) > 1 else "no"
        rows.append(row)

    RAW_OUT.write_text(json.dumps(raw, indent=2))
    with open(CSV_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    generics = sorted({r["matched_generic"] for r in rows})
    print(f"\n{len(rows)} unique trials across {len(generics)} drugs "
          f"({len(terms)} search aliases)")
    print(f"  raw  -> {RAW_OUT.relative_to(ROOT)}")
    print(f"  csv  -> {CSV_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
