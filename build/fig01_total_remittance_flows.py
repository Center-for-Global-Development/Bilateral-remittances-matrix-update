"""Figure 1: total remittance inflows by recipient, 2021 vs 2024 (data/1-total-remittance-flows.js).

Countries = recipients with a World Bank received total ('rtotal') in both 2021 and 2024.
Region / income group from the Data_concordance sheet; name from the matrix.

The v1 matrix CSV stores 'rtotal' to only ~10 significant figures, so the values are
taken at full precision from the workbook's WB_remittances_received sheet (the same
World Bank series; the v2 matrix matches it exactly). The recipient set still comes
from the matrix.
"""
from __future__ import annotations

import common

FNAME = "1-total-remittance-flows.js"
REGION_ORDER = [
    "East Asia & Pacific", "Europe & Central Asia", "Latin America & Caribbean",
    "Middle East & North Africa", "North America", "South Asia", "Sub-Saharan Africa",
]
INCOME_ORDER = ["Low income", "Lower middle income", "Upper middle income", "High income"]
REGION_COLOURS = {
    "East Asia & Pacific": "#2D99B5", "Europe & Central Asia": "#0B4C5B",
    "Latin America & Caribbean": "#FFB52C", "Middle East & North Africa": "#006970",
    "North America": "#85A5AD", "South Asia": "#1A272A", "Sub-Saharan Africa": "#00896C",
    "Other": "#DFE0E2",
}


def wb_received(m) -> "pd.DataFrame":
    """Recipient x year World Bank received totals, recipients/years as present in the matrix."""
    import pandas as pd
    rt = m.groupby(["r", "year"]).rtotal.first().unstack()[[2021, 2024]]
    wb = pd.read_excel(common.WORKBOOK, sheet_name="WB_remittances_received")
    wb.columns = [str(c).replace(".0", "") for c in wb.columns]
    wb = wb.set_index("WB_A3")[["2021", "2024"]].rename(columns={"2021": 2021, "2024": 2024})
    full = wb.reindex(rt.index)
    rel = ((rt - full).abs() / full.abs()).max().max()
    assert rel < 1e-8, f"matrix rtotal disagrees with WB_remittances_received (rel {rel})"
    return full.where(rt.notna())


def build(version: str) -> dict:
    m = common.load_matrix(version)
    conc = common.load_concordance().set_index("WB_A3")
    both = wb_received(m).dropna().sort_index()
    names = m.groupby("r").rname.first()

    countries = []
    for r, row in both.iterrows():
        raw21, raw24 = float(row[2021]), float(row[2024])
        v21, v24 = round(raw21, 2), round(raw24, 2)
        change = round(raw24 - raw21, 2)
        pct = round((raw24 - raw21) / raw21, 8) if raw21 else None
        countries.append({
            "id": r,
            "name": names[r],
            "region": conc.loc[r, "WB region"],
            "income": conc.loc[r, "WB income group"],
            "v2021": v21,
            "v2024": v24,
            "change": change,
            "pctChange": pct,
        })
    n = len(countries)
    inc = sum(c["change"] > 0 for c in countries)
    dec = sum(c["change"] < 0 for c in countries)
    present = {c["region"] for c in countries}
    summary = {
        "countryCount": n,
        "increased": inc,
        "decreased": dec,
        "unchanged": n - inc - dec,
        "increasedShare": round(inc / n, 14),
        "total2021": round(sum(c["v2021"] for c in countries), 2),
        "total2024": round(sum(c["v2024"] for c in countries), 2),
        "regions": [r for r in REGION_ORDER if r in present],
        "incomes": INCOME_ORDER,
    }
    return {"CGD_VIZ_DATA": {
        "summary": summary,
        "countries": countries,
        "regionOrder": REGION_ORDER,
        "regionColours": REGION_COLOURS,
    }}


if __name__ == "__main__":
    v1 = build("v1")
    common.report("fig01", v1, common.load_existing(FNAME), rtol=1e-9, atol=1e-9)
    v2 = build("v2")
    common.stage(FNAME, "v1", v1)
    common.stage(FNAME, "v2", v2)
    s1, s2 = v1["CGD_VIZ_DATA"]["summary"], v2["CGD_VIZ_DATA"]["summary"]
    for k in s1:
        if k not in ("regions", "incomes"):
            print(f"  {k}: v1={s1[k]}  v2={s2[k]}")
    ids1 = {c["id"] for c in v1["CGD_VIZ_DATA"]["countries"]}
    ids2 = {c["id"] for c in v2["CGD_VIZ_DATA"]["countries"]}
    print("  added:", sorted(ids2 - ids1), "removed:", sorted(ids1 - ids2))
    d1 = {c["id"]: c for c in v1["CGD_VIZ_DATA"]["countries"]}
    diff = [c["id"] for c in v2["CGD_VIZ_DATA"]["countries"] if c["id"] in d1 and (c["v2021"], c["v2024"]) != (d1[c["id"]]["v2021"], d1[c["id"]]["v2024"])]
    print("  countries with changed values:", diff)
