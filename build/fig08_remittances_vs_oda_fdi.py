"""
Figure 8: remittances vs. ODA and FDI (data/8-remittances-vs-oda-fdi.js, const EMBED).

EMBED = {
  countries: [{code:'ALL', name:'All countries'}, ...every country appearing in a row, sorted by name],
  rows: [[yearIdx(0=2021,1=2024), recipientIdx, sourceIdx, remittances, oda, fdi, remAvailable], ...],
  stats: {'2021'|'2024': {rows, rem, oda, fdi, fdi_count}},
}

Row inclusion (reproduces the 'ODA-FDI simplified' sheet): a corridor-year is kept when the
remittance corridor is scored/allocated, or gross ODA is reported, or net FDI is reported and
non-zero. Row order follows the matrix (year, recipient, source). Remittances are recomputed from
the matrix; ODA and FDI are non-model inputs taken from the 'ODA-FDI full' sheet of
'Remittances - ODA - FDI simple for visualisation v2.xlsx' (joined on year/recipient/source).

Values are rounded to 2 dp (Python round). Missing ODA -> 0 (the figure treats unreported ODA as
zero); missing FDI -> null; unallocated remittances (NaN in the matrix) -> 0 with
remAvailable = 0, which the figure shows as N/A. remAvailable = 1 for scored corridors, else 0. stats sums use the
unrounded values, summed sequentially in row order. (stats is not read by the figure.)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

FNAME = "8-remittances-vs-oda-fdi.js"
ODA_FDI_BOOK = common.SHEETS_V2 / "Remittances - ODA - FDI simple for visualisation v2.xlsx"
YEARS = [2021, 2024]

_odafdi_cache = None


def load_oda_fdi() -> pd.DataFrame:
    global _odafdi_cache
    if _odafdi_cache is None:
        f = pd.read_excel(ODA_FDI_BOOK, sheet_name="ODA-FDI full")
        f = f.rename(columns={"Year": "year", "Recipient WB A3": "r", "Source WB A3": "s", "ODA": "oda", "FDI": "fdi"})
        _odafdi_cache = f[["year", "r", "s", "oda", "fdi"]]
    return _odafdi_cache


def num(x):
    """Round to 2 dp; emit an int when whole (as the committed file does)."""
    v = round(float(x), 2)
    return int(v) if v == int(v) else v


def seq_sum(series) -> float:
    """Plain left-to-right float sum over non-missing values, in row order (as the committed
    stats were computed; pandas/Python sum use pairwise/compensated summation)."""
    v = series.dropna().to_numpy(dtype=float)
    return float(np.cumsum(v)[-1]) if len(v) else 0.0


def build(version: str) -> dict:
    m = common.load_matrix(version)
    m = m[m["year"].isin(YEARS)]
    of = load_oda_fdi()
    df = m.merge(of, on=["year", "r", "s"], how="left", validate="one_to_one")
    assert len(df) == len(m)

    keep = df["scored"] | df["oda"].notna() | (df["fdi"].notna() & (df["fdi"] != 0))
    df = df[keep].reset_index(drop=True)

    names = {}
    for code, nm in zip(df["r"], df["rname"]):
        names[code] = nm
    for code, nm in zip(df["s"], df["sname"]):
        names.setdefault(code, nm)
    ordered = sorted(names.items(), key=lambda kv: kv[1])
    countries = [{"code": "ALL", "name": "All countries"}] + [{"code": c, "name": n} for c, n in ordered]
    idx = {c["code"]: i for i, c in enumerate(countries)}

    rows = []
    for rec in df.itertuples(index=False):
        rows.append([
            YEARS.index(rec.year),
            idx[rec.r],
            idx[rec.s],
            num(0 if pd.isna(rec.flow) else rec.flow),  # unallocated corridors: 0 with remAvailable=0
            num(0 if pd.isna(rec.oda) else rec.oda),
            None if pd.isna(rec.fdi) else num(rec.fdi),
            1 if rec.scored else 0,
        ])

    stats = {}
    for y in YEARS:
        g = df[df["year"] == y]
        stats[str(y)] = {
            "rows": int(len(g)),
            "rem": seq_sum(g["flow"]),
            "oda": seq_sum(g["oda"]),
            "fdi": seq_sum(g["fdi"]),
            "fdi_count": int(g["fdi"].notna().sum()),
        }
    return {"EMBED": {"countries": countries, "rows": rows, "stats": stats}}


def check(consts: dict):
    e = consts["EMBED"]
    for r in e["rows"]:
        for v in r[3:6]:
            assert v is None or math.isfinite(v)
    for s in e["stats"].values():
        for v in s.values():
            assert math.isfinite(v)


if __name__ == "__main__":
    v1 = build("v1")
    check(v1)
    common.report("fig08", v1, common.load_existing(FNAME))
    v2 = build("v2")
    check(v2)
    print("staged", common.stage(FNAME, "v1", v1))
    print("staged", common.stage(FNAME, "v2", v2))
    for v, c in (("v1", v1), ("v2", v2)):
        e = c["EMBED"]
        print(v, "countries", len(e["countries"]), "rows", len(e["rows"]), "stats", e["stats"])
