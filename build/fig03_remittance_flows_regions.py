"""Figure 3: allocated bilateral flows by source x recipient World Bank region
(data/3-remittance-flows-regions.js). The shared builder here is also used by figure 4.

Definitions (reverse-engineered from the committed payload, checked against v1):
  * group of a country = Data_concordance 'WB region' / 'WB income group' via WB_A3.
  * cells[year|recipientGroup|sourceGroup]: value = sum of bilateral flows, share = value /
    global total of flows for the year, corridors = number of corridors with flow > 0.
  * rowTotals / colTotals = sums over recipient / source group; globalTotals = sum of all flows.
  * maxShare[year] = largest cell share.
  * topCorridors: the 12 largest positive corridors in the cell (flows written at 15
    significant figures), totalCount = positive corridors, remainingValue = cell value minus
    the listed items.
  * changeTopCorridors (figure 4 only): corridors whose flow changed 2021->2024 (missing in a
    year = 0), top 12 by |change|; value = current - previous (both at 15 s.f.), pctChange =
    value / previous (null when previous is 0); remainingValue = net cell change minus items.
"""
from __future__ import annotations

import math

import common

FNAME = "3-remittance-flows-regions.js"
YEARS = ["2021", "2024"]
TOP_N = 12
REGION_GROUPS = [
    ("EAP", "East Asia & Pacific"), ("ECA", "Europe & Central Asia"),
    ("LAC", "Latin America & Caribbean"), ("MENA", "Middle East & North Africa"),
    ("NAC", "North America"), ("SAS", "South Asia"), ("SSA", "Sub-Saharan Africa"),
]


# The committed payloads carry country names that were UTF-8 decoded as Windows-1252
# ("CuraÃ§ao", "CÃ´te d'Ivoire"). Reproduce that for the v1 check; the v2 payload gets the
# correct names unless KEEP_MOJIBAKE_V2 is set.
KEEP_MOJIBAKE_V2 = False


def mojibake(name: str) -> str:
    if name.isascii():
        return name
    out = []
    for b in name.encode("utf8"):
        try:
            out.append(bytes([b]).decode("cp1252"))
        except UnicodeDecodeError:
            out.append(chr(b))
    return "".join(out)


def names_fn(version: str):
    return mojibake if (version == "v1" or KEEP_MOJIBAKE_V2) else (lambda n: n)


def g15(x: float) -> float:
    """15 significant figures, truncated from the shortest repr. The committed payloads look
    like they passed through Excel's 15-digit precision; this reproduces most of them to the
    last digit and all of them to ~1e-14 relative (the rest is last-digit float noise)."""
    if x == 0 or not math.isfinite(x):
        return float(x)
    from decimal import Decimal, ROUND_DOWN
    d = Decimal(repr(float(x)))
    q = Decimal(1).scaleb(d.adjusted() - 14)
    return float(d.quantize(q, rounding=ROUND_DOWN))


def build_group_matrix(version: str, groups, conc_col: str, with_change: bool = False,
                       global_g15: bool = False) -> dict:
    m = common.load_matrix(version)
    conc = common.load_concordance().set_index("WB_A3")
    label_to_id = {label: gid for gid, label in groups}
    m["rg"] = m.r.map(conc[conc_col]).map(label_to_id)
    m["sg"] = m.s.map(conc[conc_col]).map(label_to_id)
    # A country with no group in the concordance (v2: Venezuela has no WB income group but now
    # sends floor-allocated flows) cannot be placed in the grid; its corridors are left out,
    # so the global total stays equal to the sum of the cells.
    unmapped = m[(m.rg.isna() | m.sg.isna()) & (m.flow > 0)]
    if not unmapped.empty:
        who = sorted(set(unmapped.loc[unmapped.rg.isna(), "r"]) | set(unmapped.loc[unmapped.sg.isna(), "s"]))
        amt = unmapped.groupby("year").flow.sum().to_dict()
        print(f"  WARNING [{version}] {len(unmapped)} positive corridors involve countries with no "
              f"{conc_col} ({who}); excluded from the grid: {amt}")
    m = m[m.rg.notna() & m.sg.notna()].copy()
    m["yr"] = m.year.astype(int).astype(str)
    fix = names_fn(version)
    m["rname"] = m.rname.map(fix)
    m["sname"] = m.sname.map(fix)
    ids = [g for g, _ in groups]

    glob = {y: float(m.loc[m.yr == y, "flow"].sum()) for y in YEARS}
    cells, top = {}, {}
    for y in YEARS:
        my = m[m.yr == y]
        by = {k: g for k, g in my.groupby(["rg", "sg"])}
        for rg in ids:
            for sg in ids:
                key = f"{y}|{rg}|{sg}"
                g = by.get((rg, sg))
                if g is None:
                    continue
                value = float(g.flow.sum())
                pos = g[g.flow > 0].sort_values("flow", ascending=False, kind="mergesort")
                cells[key] = {"year": y, "recipientGroup": rg, "sourceGroup": sg, "value": value,
                              "share": value / glob[y], "corridors": int(len(pos))}
                items = [{"source": r.sname, "recipient": r.rname, "value": g15(r.flow)}
                         for r in pos.head(TOP_N).itertuples()]
                top[key] = {"items": items, "totalCount": int(len(pos)), "shownCount": len(items),
                            "remainingValue": value - sum(i["value"] for i in items)}

    def totals(col):
        out = {}
        for y in YEARS:
            s = m[m.yr == y].groupby(col).flow.sum()
            for gid in ids:
                if gid in s.index:
                    out[f"{y}|{gid}"] = float(s[gid])
        return out

    out = {
        "groups": [{"id": g, "label": l} for g, l in groups],
        "years": YEARS,
        "cells": cells,
        "rowTotals": totals("rg"),
        "colTotals": totals("sg"),
        "globalTotals": {y: (g15(v) if global_g15 else v) for y, v in glob.items()},
        "maxShare": {y: max(c["share"] for c in cells.values() if c["year"] == y) for y in YEARS},
        "topCorridors": top,
    }
    if with_change:
        out["changeTopCorridors"] = change_top(m, ids)
        out["changeMeta"] = {"label": "Change", "fromYear": "2021", "toYear": "2024"}
    return out


def change_top(m, ids) -> dict:
    w = m.pivot_table(index=["r", "s"], columns="yr", values="flow", aggfunc="sum")
    w = w.reindex(columns=YEARS).fillna(0.0)
    meta = m.drop_duplicates(["r", "s"]).set_index(["r", "s"])[["rg", "sg", "rname", "sname"]]
    w = w.join(meta)
    w["prev"] = w["2021"].map(g15)
    w["cur"] = w["2024"].map(g15)
    w["chg"] = w["cur"] - w["prev"]
    out = {}
    for rg in ids:
        for sg in ids:
            g = w[(w.rg == rg) & (w.sg == sg)]
            net = float(g["2024"].sum() - g["2021"].sum())
            nz = g[g.chg != 0].copy()
            nz["abs"] = nz.chg.abs()
            nz = nz.sort_values("abs", ascending=False, kind="mergesort")
            items = []
            for r in nz.head(TOP_N).itertuples():
                items.append({"source": r.sname, "recipient": r.rname, "value": float(r.chg),
                              "previousValue": float(r.prev), "currentValue": float(r.cur),
                              "pctChange": (float(r.chg) / r.prev) if r.prev else None})
            out[f"change|{rg}|{sg}"] = {"items": items, "totalCount": int(len(nz)), "shownCount": len(items),
                                        "remainingValue": net - sum(i["value"] for i in items)}
    return out


def build(version: str) -> dict:
    return {"vizData": build_group_matrix(version, REGION_GROUPS, "WB region")}


def summarise(name, v1, v2):
    a, b = v1["vizData"], v2["vizData"]
    print(f"  [{name}] globalTotals v1={a['globalTotals']}  v2={b['globalTotals']}")
    print(f"  [{name}] maxShare v1={a['maxShare']}  v2={b['maxShare']}")
    for k in a["rowTotals"]:
        print(f"    rowTotal {k}: v1={a['rowTotals'][k]/1e9:.2f}bn v2={b['rowTotals'].get(k, float('nan'))/1e9:.2f}bn"
              f"   colTotal v1={a['colTotals'][k]/1e9:.2f}bn v2={b['colTotals'].get(k, float('nan'))/1e9:.2f}bn")
    n1 = sum(c["corridors"] for c in a["cells"].values())
    n2 = sum(c["corridors"] for c in b["cells"].values())
    print(f"  [{name}] positive corridors (both years) v1={n1} v2={n2}; cells v1={len(a['cells'])} v2={len(b['cells'])}")
    names = {i["recipient"] for t in b["topCorridors"].values() for i in t["items"]}
    print(f"  [{name}] South Sudan / Yemen in any v2 top-corridor list:", "South Sudan" in names, "Yemen, Rep." in names)
    bad = [k for k, c in b["cells"].items() if not all(math.isfinite(c[f]) for f in ("value", "share"))]
    print(f"  [{name}] non-finite v2 cells: {bad}")


if __name__ == "__main__":
    v1 = build("v1")
    common.report("fig03", v1, common.load_existing(FNAME), rtol=1e-9, atol=1e-6)
    v2 = build("v2")
    common.stage(FNAME, "v1", v1)
    common.stage(FNAME, "v2", v2)
    summarise("fig03", v1, v2)
