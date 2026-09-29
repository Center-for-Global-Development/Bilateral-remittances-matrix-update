"""Figure 7: how important each source country is to the recipients it sends to.

For source s and year t, over its scored (allocated) corridors r:
  share_r   = F_{s,r,t} / R_{r,t}   (R = recipient's scored inflows, i.e. its allocated total)
  avg       = sum_r share_r * F_{s,r,t} / O_{s,t}   (O = source's scored outflows)
  top       = max_r share_r
Corridor GNI shares divide the flow by the recipient's GNI in current US$ (World Bank
GNI current US$ sheet), falling back to the latest earlier year when the target year is blank.
Corridors are recipients scored in either year, ordered by 2024 share (descending); sources
are those with scored corridors in both years, ordered by name.
"""

from __future__ import annotations

import math
import statistics

import pandas as pd

import common

FNAME = "7-remittance-source-importance.js"
REGIONS = ["East Asia & Pacific", "Europe & Central Asia", "Latin America & Caribbean",
           "Middle East & North Africa", "North America", "South Asia", "Sub-Saharan Africa"]
INCOMES = ["Low income", "Lower middle income", "Upper middle income", "High income"]
# Fall back to the latest earlier year with a value, however old (all 78,966 v1 rows get a
# denominator: SSD uses 2015, YEM 2018). Status wording follows figure 9's payload.
MAX_LAG = 60


def _mojibake(name: str) -> str:
    """The committed payload's names were UTF-8 bytes decoded as Latin-1 ("CuraÃ§ao")."""
    try:
        return name.encode("utf8").decode("latin1")
    except UnicodeError:
        return name


def _lag_status(k: int) -> str:
    return "target_year" if k == 0 else ("lag_1_year" if k == 1 else f"lag_{k}_years")


def load_gni_usd() -> dict:
    g = pd.read_excel(common.GNI_CURRENT_USD, header=3)
    g = g.set_index(g["Country Code"].astype(str).str.strip())
    return {c: g[c] for c in g.columns if str(c).isdigit()}


def gni_lookup(gni: dict, code: str, year: int):
    for k in range(MAX_LAG + 1):
        col = gni.get(str(year - k))
        if col is None:
            continue
        v = col.get(code)
        if v is not None and not pd.isna(v) and v > 0:
            return float(v), year - k, _lag_status(k)
    return None, None, None


def build(version: str, legacy_names: bool = False, matrix: pd.DataFrame | None = None) -> dict:
    """legacy_names=True reproduces the committed payload's mis-encoded names exactly."""
    m = common.load_matrix(version) if matrix is None else matrix
    conc = common.load_concordance().set_index("WB_A3")
    region = conc["WB region"].to_dict()
    income = conc["WB income group"].where(conc["WB income group"].notna(), "N/A").to_dict()
    names = dict(zip(m["r"], m["rname"]))
    names.update(dict(zip(m["s"], m["sname"])))
    if legacy_names:
        names = {k: _mojibake(v) for k, v in names.items()}

    gni = load_gni_usd()
    look = {(r, y): gni_lookup(gni, r, int(y)) for r, y in m[["r", "year"]].drop_duplicates().itertuples(index=False)}
    den = m.apply(lambda x: look[(x["r"], x["year"])][0], axis=1)
    gni_rows = int(den.notna().sum())
    pos_missing = int(((m["flow"] > 0) & den.isna()).sum())

    sc = m[m["scored"]].copy()
    sc["sh"] = sc["flow"] / sc.groupby(["r", "year"])["flow"].transform("sum")
    sc["out"] = sc.groupby(["s", "year"])["flow"].transform("sum")
    sc["w"] = sc["flow"] / sc["out"]

    metrics = {}
    for (s, y), g in sc.groupby(["s", "year"]):
        top = g.loc[g["sh"].idxmax()]
        metrics[(s, y)] = {"total": float(g["flow"].sum()), "corridors": int(len(g)),
                           "avg": float((g["sh"] * g["w"]).sum()),
                           "top": float(top["sh"]), "topRecipient": names[top["r"]]}

    rowinfo = {(x.s, x.r, x.year): x for x in m[["s", "r", "year", "flow"]].itertuples(index=False)}

    both = sorted({s for s, y in metrics if y == 2021} & {s for s, y in metrics if y == 2024},
                  key=lambda s: names[s])
    countries, corridors = [], {}
    for s in both:
        a, b = metrics[(s, 2021)], metrics[(s, 2024)]
        g = sc[sc["s"] == s]
        sh = {y: dict(zip(g[g["year"] == y]["r"], g[g["year"] == y]["sh"])) for y in (2021, 2024)}
        val = {y: dict(zip(g[g["year"] == y]["r"], g[g["year"] == y]["flow"])) for y in (2021, 2024)}
        rows, keys = [], {}
        for r in sorted(set(sh[2021]) | set(sh[2024])):
            rec = {"recipient": r, "recipientName": names[r], "recipientRegion": region.get(r),
                   "recipientIncome": income.get(r, "N/A")}
            for y in (2021, 2024):
                rec[f"share{y}"] = float(sh[y].get(r, 0.0))
            for y in (2021, 2024):
                rec[f"value{y}"] = float(val[y].get(r, 0.0))
            gs = {}
            for y in (2021, 2024):
                present = (s, r, y) in rowinfo
                d, gy, st = look[(r, y)] if present else (None, None, None)
                gs[y] = rec[f"value{y}"] / d if d and rec[f"value{y}"] > 0 else None
                rec[f"gniShare{y}"] = gs[y]
            for y in (2021, 2024):
                present = (s, r, y) in rowinfo
                rec[f"gniYear{y}"] = look[(r, y)][1] if present else None
            for y in (2021, 2024):
                present = (s, r, y) in rowinfo
                rec[f"gniStatus{y}"] = look[(r, y)][2] if present else None
            rec["changeShare"] = rec["share2024"] - rec["share2021"]
            rec["changeValue"] = rec["value2024"] - rec["value2021"]
            rec["changeGniShare"] = gs[2024] - gs[2021] if gs[2024] is not None and gs[2021] is not None else None
            keys[r] = rec["share2024"]
            rows.append(rec)
        rows.sort(key=lambda d: -keys[d["recipient"]])
        corridors[s] = rows

        gni24 = [(d["gniShare2024"], d["recipientName"]) for d in rows if d["gniShare2024"] is not None]
        mx = max(gni24, key=lambda t: t[0]) if gni24 else (None, None)
        countries.append({
            "id": s, "name": names[s], "region": region.get(s), "income": income.get(s, "N/A"),
            "total2021": a["total"], "total2024": b["total"],
            "corridors2021": a["corridors"], "corridors2024": b["corridors"],
            "avg2021": a["avg"], "avg2024": b["avg"], "avgChange": b["avg"] - a["avg"],
            "top2021": a["top"], "top2024": b["top"], "topChange": b["top"] - a["top"],
            "topRecipient2021": a["topRecipient"], "topRecipient2024": b["topRecipient"],
            "maxGniShare2024": mx[0], "maxGniRecipient2024": mx[1],
        })

    summary = {
        "rowCount": int(len(m)), "scoredRows": int(m["scored"].sum()),
        "sourceYears": len(metrics), "sourcesCompared": len(countries),
        "largestRecipientChanged": sum(c["topRecipient2021"] != c["topRecipient2024"] for c in countries),
        "medianAvg2021": statistics.median(c["avg2021"] for c in countries),
        "medianAvg2024": statistics.median(c["avg2024"] for c in countries),
        "medianAvgChange": statistics.median(c["avgChange"] for c in countries),
        "medianTopChange": statistics.median(c["topChange"] for c in countries),
        "medianMaxGniShare2024": statistics.median(c["maxGniShare2024"] for c in countries
                                                   if c["maxGniShare2024"] is not None),
        "regions": REGIONS, "incomes": INCOMES,
        "gniRowsWithDenominator": gni_rows, "positiveRowsMissingGniDenominator": pos_missing,
    }
    return {"CGD_VIZ_DATA": {"summary": summary, "countries": countries, "corridors": corridors}}


if __name__ == "__main__":
    committed = common.load_existing(FNAME)
    v1 = build("v1", legacy_names=True)
    common.report("fig07", v1, committed)
    print("  with corrected (UTF-8) names instead:", end=" ")
    common.report("fig07-fixed-names", build("v1"), committed, show=0)
    v2 = build("v2")
    print(common.stage(FNAME, "v1", v1))
    print(common.stage(FNAME, "v2", v2))
