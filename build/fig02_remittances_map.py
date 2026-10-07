"""Figure 2 (2-remittances-map.html): the corridor flow map.

Two payloads (README "The map"):
  data/2-remittances-map.js          const CGD_VIZ_DATA    everything needed to draw
  data/2-remittances-map-details.js  const CGD_VIZ_DETAILS per-corridor popup stats

CGD_VIZ_DATA
  countries        every concordance row, in concordance order:
                   code=WB_A3, iso3=ISO_A3, name='Flourish country name',
                   m49=3-digit zero-padded string (None if missing),
                   region='WB region', income='WB income group'; missing text -> 'N/A'
  flows            every scored corridor-year (status in common.SCORED_STATUSES), in
                   matrix row order: {y, s, r, v=round(flow)}
  regions          sorted distinct concordance 'WB region'
  totalsByYear     {"2021": sum of the rounded flow v's, ...}
  availability     per year, codes appearing in that year's flows, in order of first
                   appearance (recipient before source within a row):
                   {received: is a recipient of a flow, sent: is a source of a flow}
  recipientAnchors per year, recipients with Total recipient remittances > 0,
                   sorted by code: unrounded total
CGD_VIZ_DETAILS
  "S|R" for each corridor pair with a scored flow in either year, keyed in order of first
  appearance in flows; {s, r, y: {year: stats}} for EVERY matrix row of that pair
  (including unscored years), years in matrix order:
    v round(flow), p share (% of recipient total) rounded to 6 dp (None if NaN),
    m round(migrant stock), status (raw allocation status string), rt round(recipient
    total), gr/gs round(GNI per capita PPP, recipient/source), gd = gs - gr,
    gp = gd / gr (unrounded). Missing numbers -> None.
"""

from __future__ import annotations

import math
import sys

import pandas as pd

import common

FNAME_MAP = "2-remittances-map.js"
FNAME_DETAILS = "2-remittances-map-details.js"

# The v1 CSV at common.MATRIX_PATHS['v1'] was found (29 Sep 2026, mid-session) to hold
# v2-model content (it contains 'scored_source_income_missing_floor' and matches the v2
# build). The full v1 long matrix survives as the 'Remittances' sheet of the v1-built
# 'Remittances - ODA - FDI full v2.xlsx' (identical columns; 17,130 scored_allocated rows,
# totals 735.0bn / 893.9bn, matching the committed figures), so v1 falls back to it.
V1_STANDIN = (common.SHEETS_V2 / "Remittances - ODA - FDI full v2.xlsx", "Remittances")


def load_matrix(version: str) -> pd.DataFrame:
    m = common.load_matrix(version)
    if version == "v1" and (m["status"] == "scored_source_income_missing_floor").any():
        print("  WARNING: v1 CSV contains v2 statuses; using v1 stand-in sheet "
              f"'{V1_STANDIN[1]}' of {V1_STANDIN[0].name}", file=sys.stderr)
        m = pd.read_excel(V1_STANDIN[0], sheet_name=V1_STANDIN[1])
        m = m.rename(columns={k: v for k, v in common.SHORT_COLUMNS.items() if k in m.columns})
        m["scored"] = m["status"].isin(common.SCORED_STATUSES)
    return m


def rint(x):
    """Python round() to int (half-to-even, as the committed values are); NaN -> None."""
    if x is None or pd.isna(x):
        return None
    return int(round(float(x)))


def rnd(x, nd):
    return None if pd.isna(x) else round(float(x), nd)


def txt(v):
    return v.strip() if isinstance(v, str) and v.strip() else "N/A"


def countries() -> list:
    con = common.load_concordance()
    out = []
    for _, r in con.iterrows():
        m49 = r["UN M49 Code"]
        out.append({
            "code": r["WB_A3"],
            "iso3": txt(r["ISO_A3"]),
            "name": txt(r["Flourish country name"]),
            "m49": f"{int(m49):03d}" if pd.notna(m49) else None,
            "region": txt(r["WB region"]),
            "income": txt(r["WB income group"]),
        })
    return out, sorted(con["WB region"].dropna().unique().tolist())


def build(version: str) -> dict:
    m = load_matrix(version).reset_index(drop=True)
    cs, regions = countries()
    sc = m[m["scored"]]

    flows = [{"y": int(y), "s": s, "r": r, "v": rint(v)}
             for y, s, r, v in zip(sc["year"], sc["s"], sc["r"], sc["flow"])]
    years = sorted(m["year"].unique())
    totals = {str(y): sum(f["v"] for f in flows if f["y"] == y) for y in years}

    availability, anchors = {}, {}
    for y in years:
        fy = [f for f in flows if f["y"] == y]
        R = {f["r"] for f in fy}
        S = {f["s"] for f in fy}
        order = list(dict.fromkeys(c for f in fy for c in (f["r"], f["s"])))
        availability[str(y)] = {c: {"received": c in R, "sent": c in S} for c in order}
        rt = m[m["year"] == y].groupby("r")["rtotal"].first()
        rt = rt[rt > 0].sort_index()
        anchors[str(y)] = {c: float(v) for c, v in rt.items()}

    data = {
        "countries": cs,
        "flows": flows,
        "regions": regions,
        "totalsByYear": totals,
        "availability": availability,
        "recipientAnchors": anchors,
    }

    # details
    pair_order = list(dict.fromkeys(f"{s}|{r}" for s, r in zip(sc["s"], sc["r"])))
    pairs = set(pair_order)
    details = {k: None for k in pair_order}
    keys = m["s"] + "|" + m["r"]
    sub = m[keys.isin(pairs)]
    for row in sub.itertuples(index=False):
        k = f"{row.s}|{row.r}"
        if details[k] is None:
            details[k] = {"s": row.s, "r": row.r, "y": {}}
        gr, gs = rint(row.gni_r), rint(row.gni_s)
        gd = gs - gr if gr is not None and gs is not None else None
        gp = gd / gr if gd is not None and gr else None
        details[k]["y"][str(int(row.year))] = {
            "v": rint(row.flow),
            "p": rnd(row.share_pct, 6),
            "m": rint(row.stock),
            "status": row.status,
            "rt": rint(row.rtotal),
            "gr": gr,
            "gs": gs,
            "gd": gd,
            "gp": gp,
        }
    return {FNAME_MAP: {"CGD_VIZ_DATA": data}, FNAME_DETAILS: {"CGD_VIZ_DETAILS": details}}


def summary(tag, out):
    d = out[FNAME_MAP]["CGD_VIZ_DATA"]
    x = out[FNAME_DETAILS]["CGD_VIZ_DETAILS"]
    ent = [e for p in x.values() for e in p["y"].values()]
    print(f"  {tag}: flows {len(d['flows'])}, totals {d['totalsByYear']}, "
          f"availability {[len(v) for v in d['availability'].values()]}, "
          f"anchors {[len(v) for v in d['recipientAnchors'].values()]}, "
          f"detail pairs {len(x)}, detail pair-years {len(ent)}")
    for c in ("SSD", "YEM"):
        n = [f for f in d["flows"] if f["r"] == c]
        print(f"    recipient {c}: {len(n)} flows, "
              f"{sum(f['v'] for f in n)/1e6:.1f}m; received flag "
              f"{[d['availability'][y].get(c, {}).get('received') for y in d['availability']]}")
    nulls = {f: sum(e[f] is None for e in ent) for f in ("v", "p", "m", "rt", "gr", "gs", "gd", "gp")}
    print(f"    detail nulls {nulls}")
    from collections import Counter
    print(f"    detail statuses {dict(Counter(e['status'] for e in ent))}")


# Per-corridor-year fields the popups never read; summary() above still reports on them.
UNUSED_DETAIL = ("status", "rt", "gr", "gs")


def trim(fname: str, consts: dict) -> dict:
    """The payload as staged. Only the details file changes."""
    if fname != FNAME_DETAILS:
        return consts
    det = consts["CGD_VIZ_DETAILS"]
    return {"CGD_VIZ_DETAILS": {
        k: {**p, "y": {y: {f: v for f, v in e.items() if f not in UNUSED_DETAIL} for y, e in p["y"].items()}}
        for k, p in det.items()
    }}


if __name__ == "__main__":
    v1 = build("v1")
    n = 0
    for fname, consts in v1.items():
        n += common.report(fname, consts, common.load_existing(fname), rtol=1e-9, atol=0)
        common.stage(fname, "v1", trim(fname, consts))
    summary("v1", v1)
    v2 = build("v2")
    for fname, consts in v2.items():
        common.stage(fname, "v2", trim(fname, consts))
    summary("v2", v2)
