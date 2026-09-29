"""Figure 12 (12-model-v-wb.html): modelled remittance outflows by source vs World Bank remittances paid.

The committed payload is not a data/ file: it is the `rawData` array written inline
in 12-model-v-wb.html. It is staged here as fname "12-model-v-wb.js" with the single
const "rawData" (a list of one dict per source country, sorted by country name).

Fields, per source country in the matrix (every Source WB A3, 214 in v1):
  code        Source WB A3
  country     concordance "WB country" (== matrix "Source country name")
  income      concordance "WB income group"; missing -> "Not classified" (Venezuela)
  model2021/  sum over recipients of Bilateral remittances (current US$) for that
  model2024   source and year (unrounded float)
  wbPaid2021/ World Bank "Personal remittances, paid (current US$)" from the source
  wbPaid2024  workbook sheet WB_remittances_paid; missing -> 0.0 (as committed; the
              figure treats 0 as "WB reports zero")
"""

from __future__ import annotations

import json

import pandas as pd

import common
from fig02_remittances_map import load_matrix  # v1 falls back to the v1 stand-in sheet (see there)

FNAME = "12-model-v-wb.js"
YEARS = (2021, 2024)


def load_committed() -> dict:
    t = (common.REPO / "12-model-v-wb.html").read_text(encoding="utf8")
    key = "const rawData = "
    val, _ = json.JSONDecoder().raw_decode(t[t.index(key) + len(key):])
    return {"rawData": val}


def wb_paid() -> pd.DataFrame:
    w = pd.read_excel(common.WORKBOOK, sheet_name="WB_remittances_paid")
    w["WB_A3"] = w["WB_A3"].astype(str).str.strip()
    w = w.set_index("WB_A3")
    w.columns = [int(float(c)) if str(c).replace(".0", "").isdigit() else c for c in w.columns]
    return w


def build(version: str) -> dict:
    m = load_matrix(version)
    con = common.load_concordance().set_index("WB_A3")
    wb = wb_paid()
    model = m.groupby(["s", "year"])["flow"].sum().unstack("year")
    names = con["WB country"]
    rows = []
    for code in model.index:
        inc = con.loc[code, "WB income group"] if code in con.index else None
        if not isinstance(inc, str) or not inc.strip():
            inc = "Not classified"
        d = {"code": code, "country": names[code], "income": inc}
        for y in YEARS:
            d[f"model{y}"] = float(model.loc[code, y]) if pd.notna(model.loc[code, y]) else 0.0
        for y in YEARS:
            v = wb.loc[code, y] if code in wb.index else float("nan")
            d[f"wbPaid{y}"] = float(v) if pd.notna(v) else 0.0
        rows.append(d)
    rows.sort(key=lambda d: d["country"])
    return {"rawData": rows}


if __name__ == "__main__":
    v1 = build("v1")
    common.report("fig12", v1, load_committed(), rtol=1e-9, atol=1e-6)
    common.stage(FNAME, "v1", v1)
    v2 = build("v2")
    common.stage(FNAME, "v2", v2)
    a = {d["code"]: d for d in v1["rawData"]}
    b = {d["code"]: d for d in v2["rawData"]}
    for y in YEARS:
        print(f"model{y} total: v1 {sum(d[f'model{y}'] for d in a.values())/1e9:.3f}bn  "
              f"v2 {sum(d[f'model{y}'] for d in b.values())/1e9:.3f}bn;  "
              f"wbPaid{y} total {sum(d[f'wbPaid{y}'] for d in b.values())/1e9:.3f}bn")
    print("rows v1", len(a), "v2", len(b))
