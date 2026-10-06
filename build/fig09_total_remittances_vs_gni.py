"""Figure 9: total remittance inflows relative to current-US$ GNI, 2021 vs 2024
(data/9-total-remittances-vs-gni.js).

Definitions (reverse-engineered from the committed payload, checked against v1):
  * countries = recipients with a World Bank received total in both years (as figure 1),
    sorted by WB_A3; name from the matrix, region / income from Data_concordance.
  * total{year} = World Bank received total (15 s.f.), from WB_remittances_received.
  * gni{year} = World Bank GNI, current US$ (common.GNI_CURRENT_USD); if the target year
    is blank, the latest earlier year, with gniYear / gniLag ("target_year",
    "lag_1_year", "lag_N_years") recording which.
  * ratio{year} = total / gni; changePp = (ratio2024 - ratio2021) * 100.
  * partialCoverage = matrix "Partial migrant-stock coverage, recipient?" (either year).
  * components = sources with a positive modelled flow in either year, sorted by 2024 flow
    (desc); values at 15 s.f.; pctGni = value / gni; share = value / total.
    sources = number of components; largestSource{year} = first component by that year's
    value (null when there are none); largestSourceShare2024 = its 2024 share.
  * summary: rows = matrix rows; pairedRecipients = countries; maxRatio over both years;
    maxTotal2024; medians of ratio; counts of ratio2024 >, <, == ratio2021; counts of
    ratio2024 above 10% and 25%.
"""
from __future__ import annotations

import math
import statistics

import pandas as pd

import common
from fig01_total_remittance_flows import INCOME_ORDER, REGION_ORDER, wb_received
from fig03_remittance_flows_regions import g15, names_fn

FNAME = "9-total-remittances-vs-gni.js"
YEARS = (2021, 2024)
UNCLASSIFIED = None  # value written for a source with no concordance region / income group


def load_gni() -> pd.DataFrame:
    g = pd.read_excel(common.GNI_CURRENT_USD, header=3)
    g = g.set_index("Country Code")
    g.columns = [str(c) for c in g.columns]
    return g


def lag_label(n: int) -> str:
    return "target_year" if n == 0 else ("lag_1_year" if n == 1 else f"lag_{n}_years")


def gni_for(g: pd.DataFrame, iso: str, year: int):
    if iso not in g.index:
        return None, None, None
    row = g.loc[iso]
    for y in range(year, 1959, -1):
        v = row.get(str(y))
        if v is not None and pd.notna(v):
            return float(v), y, lag_label(year - y)
    return None, None, None


def nz(x):
    return None if (x is None or (isinstance(x, float) and math.isnan(x))) else x


def build(version: str) -> dict:
    m = common.load_matrix(version)
    conc = common.load_concordance().set_index("WB_A3")
    gni = load_gni()
    fix = names_fn(version)
    totals = wb_received(m).dropna().sort_index()
    names = m.groupby("r").rname.first()
    snames = m.groupby("s").sname.first()
    partial = m.groupby("r").partial_r.any()
    flows = m.pivot_table(index=["r", "s"], columns="year", values="flow", aggfunc="sum")
    flows = flows.reindex(columns=list(YEARS)).fillna(0.0)
    recips = set(flows.index.get_level_values(0))

    def group(s, col):
        return nz(conc[col].get(s)) if s in conc.index else None

    countries = []
    for r, trow in totals.iterrows():
        tot = {y: g15(float(trow[y])) for y in YEARS}
        gv = {y: gni_for(gni, r, y) for y in YEARS}
        g = {y: gv[y][0] for y in YEARS}
        ratio = {y: (tot[y] / g[y] if g[y] else None) for y in YEARS}
        comps = []
        if r in recips:
            f = flows.loc[r]
            f = f[(f[2021] > 0) | (f[2024] > 0)]
            f = f.assign(v21=f[2021].map(g15), v24=f[2024].map(g15))
            f = f.sort_values("v24", ascending=False, kind="mergesort")
            for s, fr in f.iterrows():
                comps.append({
                    "sourceId": s,
                    "sourceName": fix(snames[s]),
                    "sourceRegion": group(s, "WB region") or UNCLASSIFIED,
                    "sourceIncome": group(s, "WB income group") or UNCLASSIFIED,
                    "value2021": fr.v21,
                    "value2024": fr.v24,
                    "pctGni2021": fr.v21 / g[2021] if g[2021] else None,
                    "pctGni2024": fr.v24 / g[2024] if g[2024] else None,
                    "share2021": fr.v21 / tot[2021] if tot[2021] else None,
                    "share2024": fr.v24 / tot[2024] if tot[2024] else None,
                })

        def largest(y):
            if not comps:
                return None
            return max(comps, key=lambda c: c[f"value{y}"])  # first maximum

        l21, l24 = largest(2021), largest(2024)
        countries.append({
            "id": r,
            "name": fix(names[r]),
            "region": conc.loc[r, "WB region"],
            "income": conc.loc[r, "WB income group"],
            "total2021": tot[2021],
            "total2024": tot[2024],
            "gni2021": g[2021],
            "gni2024": g[2024],
            "ratio2021": ratio[2021],
            "ratio2024": ratio[2024],
            "changePp": (ratio[2024] - ratio[2021]) * 100 if None not in ratio.values() else None,
            "gniYear2021": gv[2021][1],
            "gniYear2024": gv[2024][1],
            "gniLag2021": gv[2021][2],
            "gniLag2024": gv[2024][2],
            "partialCoverage": bool(partial.get(r, False)),
            "sources": len(comps),
            "largestSource2021": l21["sourceName"] if l21 else None,
            "largestSource2024": l24["sourceName"] if l24 else None,
            "largestSourceShare2024": l24["share2024"] if l24 else None,
            "components": comps,
        })

    paired = [c for c in countries if c["ratio2021"] is not None and c["ratio2024"] is not None]
    present = {c["region"] for c in countries}
    summary = {
        "rows": int(len(m)),
        "pairedRecipients": len(paired),
        "regions": [r for r in REGION_ORDER if r in present],
        "incomes": INCOME_ORDER,
        "maxRatio": max(max(c["ratio2021"], c["ratio2024"]) for c in paired),
        "maxTotal2024": max(c["total2024"] for c in countries),
        "median2021": statistics.median(c["ratio2021"] for c in paired),
        "median2024": statistics.median(c["ratio2024"] for c in paired),
        "higher2024": sum(c["ratio2024"] > c["ratio2021"] for c in paired),
        "higher2021": sum(c["ratio2024"] < c["ratio2021"] for c in paired),
        "same": sum(c["ratio2024"] == c["ratio2021"] for c in paired),
        "above10pct2024": sum(c["ratio2024"] > 0.10 for c in paired),
        "above25pct2024": sum(c["ratio2024"] > 0.25 for c in paired),
    }
    return {"CGD_VIZ_DATA": {"summary": summary, "countries": countries}}


# Written to data/ but never read by the figure, which plots ratio2021 against ratio2024
# and has no popup. `components` alone was 97% of the payload. build() still produces
# all of them, because the v1/v2 diagnostics below read components and sources.
UNUSED_COUNTRY = ("components", "sources", "largestSource2021", "largestSource2024",
                  "largestSourceShare2024", "total2021", "gni2021", "gni2024", "changePp",
                  "gniYear2021", "gniYear2024", "gniLag2021", "gniLag2024", "partialCoverage")


def trim(out: dict) -> dict:
    d = out["CGD_VIZ_DATA"]
    return {"CGD_VIZ_DATA": {"summary": d["summary"],
                             "countries": common.drop_fields(d["countries"], UNUSED_COUNTRY)}}


if __name__ == "__main__":
    v1 = build("v1")
    common.report("fig09", v1, common.load_existing(FNAME), rtol=1e-9, atol=1e-9)
    v2 = build("v2")
    common.stage(FNAME, "v1", trim(v1))
    common.stage(FNAME, "v2", trim(v2))
    s1, s2 = v1["CGD_VIZ_DATA"]["summary"], v2["CGD_VIZ_DATA"]["summary"]
    for k in s1:
        if k not in ("regions", "incomes"):
            print(f"  {k}: v1={s1[k]}  v2={s2[k]}")
    c1 = {c["id"]: c for c in v1["CGD_VIZ_DATA"]["countries"]}
    c2 = {c["id"]: c for c in v2["CGD_VIZ_DATA"]["countries"]}
    print("  components v1=%d v2=%d" % (sum(c["sources"] for c in c1.values()),
                                        sum(c["sources"] for c in c2.values())))
    for r in ("SSD", "YEM", "NCL", "PYF", "RUS", "UKR"):
        for tag, cc in (("v1", c1), ("v2", c2)):
            c = cc.get(r)
            if c:
                print(f"  {r} {tag}: sources={c['sources']} largest2024={c['largestSource2024']} "
                      f"share={c['largestSourceShare2024']} ratio2024={c['ratio2024']:.4f}")
    nulls = [(c["id"], k["sourceId"]) for c in c2.values() for k in c["components"]
             if k["sourceIncome"] is None or k["sourceRegion"] is None]
    print(f"  v2 components with no source region/income: {len(nulls)} {sorted({s for _, s in nulls})}")
