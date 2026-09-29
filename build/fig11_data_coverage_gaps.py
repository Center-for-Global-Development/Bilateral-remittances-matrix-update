"""
Figure 11: data coverage gaps (data/11-data-coverage-gaps.js, consts DATA and MISSING_CORRIDORS).

Per year (2021, 2024), over every matrix row for that year (one row per recipient x source):
  scored     status in common.SCORED_STATUSES (v2's 'scored_source_income_missing_floor' is
             scored/allocated, so it never appears as a gap status)
  blocked    status 'blocked_corridor_zeroed';  self: status 'self_corridor_zeroed'
  gap        every other status (no stock record, source-reported zero stock, missing income,
             recipient with no positive usable score)

DATA[year] = {
  summary: {totalCorridors, recipientCount, scoredCorridors, scoredShare, noStockCorridors,
            noStockShare, gapCorridors, gapShare, allGapRecipients (recipients with 0 scored),
            partialCoverageRecipients (names, recipient order)},
  statusCounts: [{status, label, count, share=count/totalCorridors}] for gap statuses, count desc,
  recipients: [{country, code, gapShare, gapCorridors, totalCorridors, scoredCorridors,
                noStockCorridors, blockedCorridors, selfCorridors, partialCoverage,
                externalStatuses: [{status, label, count, share, examples (first 8 sources)}],
                region}] in recipient-code order,
}
MISSING_CORRIDORS[year][code] = [{status, label, sources (all, source-code order)}], same order
as externalStatuses. Status order (statusCounts and per recipient): count desc, ties by label.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

FNAME = "11-data-coverage-gaps.js"
YEARS = [2021, 2024]
N_EXAMPLES = 8

LABELS = {
    "no_stock_record_zero_allocation": "No migrant-stock record",
    "recipient_unallocated_no_positive_usable_score": "Recipient had no positive usable corridor score",
    "source_reported_zero_stock": "Source-reported zero migrant stock",
    "unscored_missing_source_income": "Missing source-country income",
    "unscored_missing_recipient_income": "Missing recipient-country income",
    "unscored_missing_recipient_and_source_income": "Missing income for both countries",
}
NON_GAP = set(common.SCORED_STATUSES) | {"blocked_corridor_zeroed", "self_corridor_zeroed"}


def ordered_counts(statuses) -> list:
    """[(status, count)] by count desc, ties by label (alphabetical)."""
    counts = {}
    for s in statuses:
        counts[s] = counts.get(s, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], LABELS[kv[0]]))


def build(version: str) -> dict:
    m = common.load_matrix(version)
    unknown = set(m["status"]) - NON_GAP - set(LABELS)
    assert not unknown, f"unlabelled statuses: {unknown}"
    conc = common.load_concordance().drop_duplicates("WB_A3").set_index("WB_A3")
    m = m.sort_values(["year", "r", "s"], kind="stable")

    data, missing = {}, {}
    for y in YEARS:
        g = m[m["year"] == y]
        g = g.assign(gap=~g["status"].isin(NON_GAP))
        total = len(g)
        recipients, miss_y = [], {}
        for code, h in g.groupby("r", sort=True):
            n = len(h)
            gap_rows = h[h["gap"]]
            ext, groups = [], []
            for st, cnt in ordered_counts(list(gap_rows["status"])):
                names = list(gap_rows.loc[gap_rows["status"] == st, "sname"])
                ext.append({"status": st, "label": LABELS[st], "count": cnt, "share": cnt / n,
                            "examples": names[:N_EXAMPLES]})
                groups.append({"status": st, "label": LABELS[st], "sources": names})
            region = conc.at[code, "WB region"] if code in conc.index else None
            recipients.append({
                "country": h["rname"].iloc[0],
                "code": code,
                "gapShare": len(gap_rows) / n,
                "gapCorridors": int(len(gap_rows)),
                "totalCorridors": int(n),
                "scoredCorridors": int(h["scored"].sum()),
                "noStockCorridors": int((h["status"] == "no_stock_record_zero_allocation").sum()),
                "blockedCorridors": int((h["status"] == "blocked_corridor_zeroed").sum()),
                "selfCorridors": int((h["status"] == "self_corridor_zeroed").sum()),
                "partialCoverage": bool(h["partial_r"].any()),
                "externalStatuses": ext,
                "region": region if isinstance(region, str) else None,
            })
            miss_y[code] = groups

        scored = int(g["scored"].sum())
        nostock = int((g["status"] == "no_stock_record_zero_allocation").sum())
        gap = int(g["gap"].sum())
        status_counts = [{"status": st, "label": LABELS[st], "count": c, "share": c / total}
                         for st, c in ordered_counts(list(g.loc[g["gap"], "status"]))]
        data[str(y)] = {
            "summary": {
                "totalCorridors": total,
                "recipientCount": len(recipients),
                "scoredCorridors": scored,
                "scoredShare": scored / total,
                "noStockCorridors": nostock,
                "noStockShare": nostock / total,
                "gapCorridors": gap,
                "gapShare": gap / total,
                "allGapRecipients": sum(1 for r in recipients if r["scoredCorridors"] == 0),
                "partialCoverageRecipients": [r["country"] for r in recipients if r["partialCoverage"]],
            },
            "statusCounts": status_counts,
            "recipients": recipients,
        }
        missing[str(y)] = miss_y
    return {"DATA": data, "MISSING_CORRIDORS": missing}


if __name__ == "__main__":
    v1 = build("v1")
    common.report("fig11", v1, common.load_existing(FNAME))
    v2 = build("v2")
    print("staged", common.stage(FNAME, "v1", v1))
    print("staged", common.stage(FNAME, "v2", v2))
    for v, c in (("v1", v1), ("v2", v2)):
        for y in YEARS:
            d = c["DATA"][str(y)]
            print(v, y, d["summary"])
            print("   ", [(s["status"], s["count"]) for s in d["statusCounts"]])
