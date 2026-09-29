"""Figure 5: migrant stock abroad vs (stock-weighted) destination GNI per capita.

Origin country = matrix recipient (r); destination = matrix source (s).
Rows used: non-self corridors with a positive migrant stock. The weighted average
destination GNI (GNI per capita, PPP, current international $, the matrix's
source GNI column) uses only destinations with a positive GNI; coverage is the
share of the origin's stock abroad sitting in such destinations.
"""

from __future__ import annotations

import math

import pandas as pd

import common

FNAME = "5-migrant-stock-vs-gni.js"
REGIONS = ["East Asia & Pacific", "Europe & Central Asia", "Latin America & Caribbean",
           "Middle East & North Africa", "North America", "South Asia", "Sub-Saharan Africa"]
INCOMES = ["Low income", "Lower middle income", "Upper middle income", "High income"]
MAX_DEST = 50


def _num(x):
    if x is None:
        return None
    x = float(x)
    return x if math.isfinite(x) else None


def _pct(new, old):
    return (new - old) / old if old else None


def build(version: str) -> dict:
    m = common.load_matrix(version)
    conc = common.load_concordance().set_index("WB_A3")
    region = conc["WB region"].to_dict()
    income = conc["WB income group"].where(conc["WB income group"].notna(), "N/A").to_dict()

    n_rows = len(m)
    self_mask = m["self"].astype(bool)
    ns = m[~self_mask]
    valid = ns[ns["stock"] > 0].copy()
    gni_ok = valid["gni_s"] > 0
    summary_counts = {
        "sourceRows": int(n_rows),
        "usedGniRows": int(gni_ok.sum()),
        "excludedSelfRows": int(self_mask.sum()),
        "skippedInvalidStockRows": int(len(ns) - len(valid)),
        "skippedInvalidGniRows": int((~gni_ok).sum()),
    }
    valid["gni_ok"] = gni_ok

    names = dict(zip(m["r"], m["rname"]))
    names.update(dict(zip(m["s"], m["sname"])))

    countries = []
    destinations = {}
    for r, g in valid.groupby("r", sort=True):
        rec = {}
        for y in (2021, 2024):
            gy = g[g["year"] == y]
            tot = gy["stock"].sum()
            gg = gy[gy["gni_ok"]]
            w = gg["stock"].sum()
            rec[y] = dict(tot=tot, avg=(gg["stock"] * gg["gni_s"]).sum() / w if w > 0 else None,
                          cov=w / tot if tot > 0 else None)
        a21, a24 = rec[2021]["avg"], rec[2024]["avg"]
        if a21 is None or a24 is None:
            continue
        m21, m24 = rec[2021]["tot"], rec[2024]["tot"]
        countries.append({
            "id": r, "name": names[r], "region": region.get(r), "income": income.get(r, "N/A"),
            "avgGni2021": a21, "avgGni2024": a24, "changeAbs": a24 - a21, "changePct": _pct(a24, a21),
            "migrants2021": m21, "migrants2024": m24, "migrantChange": m24 - m21,
            "migrantChangePct": _pct(m24, m21),
            "coverage2021": rec[2021]["cov"], "coverage2024": rec[2024]["cov"],
        })
        p = g.pivot_table(index="s", columns="year", values="stock", aggfunc="sum")
        p = p.reindex(columns=[2021, 2024])
        rows = []
        for s, st in p.iterrows():
            s21, s24 = st[2021], st[2024]
            s21 = 0.0 if pd.isna(s21) else float(s21)
            s24 = 0.0 if pd.isna(s24) else float(s24)
            rows.append({
                "id": s, "name": names[s], "income": income.get(s, "N/A"), "region": region.get(s),
                "stock2021": s21, "stock2024": s24, "stockChange": s24 - s21,
                "stockChangePct": _pct(s24, s21),
                "share2021": s21 / m21 if m21 else None, "share2024": s24 / m24 if m24 else None,
            })
        rows.sort(key=lambda d: -abs(d["stockChange"]))
        destinations[r] = rows[:MAX_DEST]

    def mm(key, fn):
        vals = [c[key] for c in countries if c[key] is not None]
        return fn(vals)

    summary = {
        "countries": len(countries), "regions": REGIONS, "incomes": INCOMES,
        "domainMin": mm("avgGni2021", min), "domainMax": mm("avgGni2021", max),
        "migrantDomainMin": mm("migrants2021", min), "migrantDomainMax": mm("migrants2021", max),
        "stockMin": mm("migrants2024", min), "stockMax": mm("migrants2024", max),
        "gniChangeMin": mm("changePct", min), "gniChangeMax": mm("changePct", max),
        "migrantChangeMin": mm("migrantChangePct", min), "migrantChangeMax": mm("migrantChangePct", max),
        **summary_counts,
        "gniUnit": "current international $",
    }
    return {"CGD_VIZ_DATA": {"summary": summary, "countries": countries, "destinations": destinations}}


if __name__ == "__main__":
    v1 = build("v1")
    common.report("fig05", v1, common.load_existing(FNAME))
    v2 = build("v2")
    print(common.stage(FNAME, "v1", v1))
    print(common.stage(FNAME, "v2", v2))
