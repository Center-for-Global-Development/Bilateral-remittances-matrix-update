"""Figure 6: how concentrated each recipient's remittance sources are, 2021 vs 2024.

For each recipient-year, shares are flow / sum of scored (allocated) flows. Metrics:
largest-corridor share (top1), top-three share (top3), Herfindahl index (hhi) and
the effective number of sources (1/hhi). Countries are recipients with scored
corridors in both years.
"""

from __future__ import annotations

import statistics

import pandas as pd

import common

FNAME = "6-remittances-source-dependence.js"
REGIONS = ["East Asia & Pacific", "Europe & Central Asia", "Latin America & Caribbean",
           "Middle East & North Africa", "North America", "South Asia", "Sub-Saharan Africa"]
INCOMES = ["Low income", "Lower middle income", "Upper middle income", "High income"]


def _mojibake(name: str) -> str:
    """The committed payload's names were UTF-8 bytes decoded as Latin-1 ("CuraÃ§ao")."""
    try:
        return name.encode("utf8").decode("latin1")
    except UnicodeError:
        return name


def build(version: str, legacy_names: bool = False) -> dict:
    """legacy_names=True reproduces the committed payload's mis-encoded names exactly."""
    m = common.load_matrix(version)
    conc = common.load_concordance().set_index("WB_A3")
    region = conc["WB region"].to_dict()
    income = conc["WB income group"].where(conc["WB income group"].notna(), "N/A").to_dict()
    names = dict(zip(m["r"], m["rname"]))
    names.update(dict(zip(m["s"], m["sname"])))
    if legacy_names:
        names = {k: _mojibake(v) for k, v in names.items()}

    sc = m[m["scored"]].copy()
    sc["tot"] = sc.groupby(["r", "year"])["flow"].transform("sum")
    sc["sh"] = sc["flow"] / sc["tot"]

    metrics = {}
    for (r, y), g in sc.groupby(["r", "year"]):
        sh = g["sh"].sort_values(ascending=False)
        hhi = float((sh ** 2).sum())
        top = g.loc[g["sh"].idxmax()]
        metrics[(r, y)] = {
            "total": float(g["rtotal"].iloc[0]),
            "top1": float(sh.iloc[0]), "top3": float(sh.iloc[:3].sum()),
            "hhi": hhi, "eff": 1.0 / hhi, "topSource": names[top["s"]],
        }

    both = sorted({r for r, y in metrics if y == 2021} & {r for r, y in metrics if y == 2024},
                  key=lambda r: names[r])
    countries, corridors = [], {}
    for r in both:
        a, b = metrics[(r, 2021)], metrics[(r, 2024)]
        rec = {"id": r, "name": names[r], "region": region.get(r), "income": income.get(r, "N/A"),
               "total2021": a["total"], "total2024": b["total"]}
        for y, mt in ((2021, a), (2024, b)):
            for k in ("top1", "top3", "hhi", "eff", "topSource"):
                rec[f"{k}{y}"] = mt[k]
        for k in ("top1", "top3", "hhi", "eff"):
            rec[f"{k}Change"] = b[k] - a[k]
        countries.append(rec)

        g = sc[sc["r"] == r]
        p = g.pivot_table(index="s", columns="year", values=["sh", "flow"], aggfunc="sum")
        rows = []
        keys = {}
        for s in p.index:
            def get(col, y):
                v = p[col].get(y, pd.Series(dtype=float)).get(s)
                return 0.0 if v is None or pd.isna(v) else float(v)
            s21, s24, v21, v24 = get("sh", 2021), get("sh", 2024), get("flow", 2021), get("flow", 2024)
            rows.append({"source": s, "sourceName": names[s], "sourceRegion": region.get(s),
                         "sourceIncome": income.get(s, "N/A"), "share2021": s21, "share2024": s24,
                         "value2021": v21, "value2024": v24, "changeShare": s24 - s21,
                         "changeValue": v24 - v21})
            # Order: 2024 share, falling back to the 2021 share for a corridor not scored in 2024.
            keys[s] = s24 if not pd.isna(p["sh"].get(2024, pd.Series(dtype=float)).get(s)) else s21
        rows.sort(key=lambda d: -keys[d["source"]])
        corridors[r] = rows

    summary = {
        "rowCount": int(len(m)), "scoredRows": int(m["scored"].sum()),
        "recipientYears": len(metrics), "countriesCompared": len(countries),
        "topSourceChanged": sum(c["topSource2021"] != c["topSource2024"] for c in countries),
        "medianTop12021": statistics.median(c["top12021"] for c in countries),
        "medianTop12024": statistics.median(c["top12024"] for c in countries),
        "medianTop1Change": statistics.median(c["top1Change"] for c in countries),
        "medianHhiChange": statistics.median(c["hhiChange"] for c in countries),
        "regions": REGIONS, "incomes": INCOMES,
    }
    return {"CGD_VIZ_DATA": {"summary": summary, "countries": countries, "corridors": corridors}}


# Written to data/ but never read by the figure: the concentration indices it does not
# plot, and per-corridor region / income it does not display.
UNUSED_COUNTRY = ("total2021", "hhi2021", "hhi2024", "hhiChange", "eff2021", "eff2024", "effChange")
UNUSED_CORRIDOR = ("sourceRegion", "sourceIncome")


def trim(out: dict) -> dict:
    """The payload as staged: build() output less unused fields, and only the corridors
    the country popup can show (common.popup_corridors). build() keeps everything so the
    checks above still see the full data."""
    d = out["CGD_VIZ_DATA"]
    return {"CGD_VIZ_DATA": {
        "summary": d["summary"],
        "countries": common.drop_fields(d["countries"], UNUSED_COUNTRY),
        "corridors": {r: common.drop_fields(common.popup_corridors(rows), UNUSED_CORRIDOR)
                      for r, rows in d["corridors"].items()},
    }}


if __name__ == "__main__":
    committed = common.load_existing(FNAME)
    v1 = build("v1", legacy_names=True)
    common.report("fig06", v1, committed)
    print("  with corrected (UTF-8) names instead:", end=" ")
    common.report("fig06-fixed-names", build("v1"), committed, show=0)
    v2 = build("v2")
    print(common.stage(FNAME, "v1", trim(v1)))
    print(common.stage(FNAME, "v2", trim(v2)))
