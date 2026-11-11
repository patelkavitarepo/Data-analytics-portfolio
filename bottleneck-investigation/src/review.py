"""Readable review artifact; observations remain separate from operational hypotheses."""

import argparse
import json
import math
from pathlib import Path
from src.analytics import metrics, summary, adjusted, persistent
from src.bundle import load_bundle


def wilson(success, n):
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    p = success / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return center - half, center + half


def report(folder):
    folder = Path(folder)
    meta, d = load_bundle(folder)
    if d is None:
        raise ValueError("Verified evidence required")
    m = metrics(d)
    monthly = summary(d.assign(month=d.created_date.str[:7]), ["month"])
    agencies = summary(d, ["agency"])
    categories = summary(d, ["category"])
    cells = adjusted(d)
    if not cells.empty:
        cells["agency_wilson_low"], cells["agency_wilson_high"] = zip(
            *(wilson(r.closed30, r.eligible30) for r in cells.itertuples())
        )
        cells["peer_wilson_low"], cells["peer_wilson_high"] = zip(
            *(wilson(r.peer_closed, r.peer_n) for r in cells.itertuples())
        )
        cells["disjoint_lower_interval"] = (
            cells.agency_wilson_high < cells.peer_wilson_low
        )
    ten = persistent(d, 10)
    fifteen = persistent(d, 15)
    candidates = ten[ten.candidate].copy()
    for name, frame in [
        ("monthly", monthly),
        ("agencies", agencies),
        ("categories", categories),
        ("comparable-cells", cells),
        ("screen-10pp", ten),
        ("screen-15pp", fifteen),
    ]:
        frame.to_csv(folder / f"{name}.csv", index=False)
    observation = {
        "metrics": m,
        "candidate_count_10pp": len(candidates),
        "candidate_count_15pp": int(fifteen.candidate.sum()),
        "comparable_cells": len(cells),
        "comparable_agency_category_pairs": len(ten),
        "candidates_10pp": candidates.to_dict(orient="records"),
        "candidates_15pp": fifteen[fifteen.candidate].to_dict(orient="records"),
    }
    (folder / "observations.json").write_text(
        json.dumps(observation, indent=2, allow_nan=False) + "\n"
    )
    missing = meta["quality"]["missing_dimensions"]["neighborhood"]
    lines = (
        [
            "# Case 002 — authentic evidence review package",
            "",
            "**Review status: unreviewed artifact. Not approved for public dashboard publication.**",
            "",
            f"Source: {meta['source_url']} · {meta['dataset_title']} ({meta['dataset_id']}).",
            f"Extraction: {meta['extraction_started_at']} → {meta['extracted_at']}; metric cutoff fixed at extraction start.",
            f"Cohort: 2025 San Francisco local creation year. Coverage: {meta['min_created_local']} through {meta['max_created_local']}.",
            f"Source counts before/after: {meta['source_count_before']:,}/{meta['source_count_after']:,}. Downloaded and unique IDs: {meta['downloaded_rows']:,}/{meta['unique_request_ids']:,}.",
            f"Pages: {meta['pages']}; aggregate rows: {meta['cube_rows']:,}; bytes: {meta['cube_bytes']:,}.",
            "",
            "## Verified observations",
            "",
            f"- Requests: {int(m['requests']):,}.",
            f"- Administrative closure within 7 days: {m['rate7']:.2%} ({int(m['closed7']):,}/{int(m['eligible7']):,} eligible requests).",
            f"- Administrative closure within 30 days: {m['rate30']:.2%} ({int(m['closed30']):,}/{int(m['eligible30']):,} eligible requests).",
            f"- Valid closed cases: {int(m['closed_valid']):,}; median ≈{m['median_days']:.0f} days; P90 ≈{m['p90_days']:.0f} days. Quantiles are floored day bins, <1 day rounding error; unresolved cases excluded from quantiles only.",
            f"- Unknown neighborhood: {missing:,} ({missing/meta['rows']:.2%}).",
            f"- Comparable agency/category pairs: {len(ten):,}; monthly cells: {len(cells):,}.",
            f"- Persistent screening candidates: {len(candidates)} at 10 points; {int(fifteen.candidate.sum())} at 15 points.",
            "",
            "## Quality ledger",
            "",
            "```json",
            json.dumps(meta["quality"], indent=2),
            "```",
            "",
            "Status counts: `" + json.dumps(meta["status_counts"]) + "`.",
            "",
            "## Candidate interpretation",
            "",
            "See screen-10pp.csv, screen-15pp.csv and comparable-cells.csv. Candidates use ≥3 comparable months, ≥90 requests, and the required deficit in ≥half the months (minimum two). Each monthly agency and other-agency category peer cell needs ≥30 eligible requests. Peer groups exclude the focal agency.",
            "Monthly 95% Wilson intervals are descriptive binomial intervals. The disjoint-interval flag indicates separation under an independent-request model, not a multiplicity-adjusted test. Repeated reporters, spatial clustering, administrative policies and coarse category mix can invalidate independence or causal interpretation. No candidate is declared a statistically proven operational failure.",
            "",
            "## Hypotheses and next checks",
            "",
            "Differences may reflect subcategory complexity, routing rules, administrative closure practices or service constraints. Validate work orders and field outcomes, inspect status histories and subcategory mix, and repeat screens with independent or clustered uncertainty estimates before operational escalation. No staffing or dispatch failure is inferred.",
            "",
            "## Limitations",
            "",
        ]
        + ["- " + x for x in meta["limitations"]]
        + [
            "- Count and update-marker reconciliation are extraction checks; the API is mutable and is not a transactional snapshot.",
            "- Public requests are reported demand, not all underlying need; geographic comparisons lack population/exposure controls.",
            "- Floating local timestamps in the repeated fall-back hour are flagged uncertain. They remain in eligible denominators but cannot count as valid closures; no unsupported timezone fold is used for success metrics.",
            "- Completeness covers the returned 2025 source cohort, not unreported, deleted or historically revised requests.",
            "",
        ]
    )
    (folder / "DATA_QUALITY_REPORT.md").write_text("\n".join(lines))
    print(
        json.dumps(
            {"event": "verified_observations", "rows": meta["rows"], **observation},
            indent=2,
        )
    )
    return observation


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    report(p.parse_args().evidence)
