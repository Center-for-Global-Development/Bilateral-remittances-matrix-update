"""
Figure 10: remittance corridors relative to recipient GNI
(data/10-remittance-corridors-vs-gni.js, const CGD_VIZ_DATA, a JSON string).

CGD_VIZ_DATA = {
  fields: [source, recipient, flow2021, flow2024, gniShare2021, gniShare2024,
           recipientRemitShare2021, recipientRemitShare2024],
  countries: {A3: {name, region, income}} for every country in a corridor, ordered by name,
  corridors: [[...fields]],
  summary: {corridors, countries, regions (sorted), incomes (sorted)},
}

A corridor is a (source, recipient) pair that is scored/allocated in 2021 or 2024. Order: the
2021 scored corridors in matrix order, then corridors scored only in 2024 in matrix order.
Year values are null where the corridor is not scored that year.
  flowYYYY                 bilateral remittances, current US$, rounded to whole dollars (float)
  gniShareYYYY             flow / recipient GNI (current US$, WDI), fraction, 12 dp
  recipientRemitShareYYYY  share of recipient total remittances, as a fraction, 14 dp. The figure's
                           normalisePercentLike() divides by 100 only above 1.5, so the percent form the
                           committed v1 file used showed any share of 1.5% or less 100x too large in the
                           popup. Fractions (all <= 1) pass through it unchanged. build(v, share_as_fraction=False)
                           reproduces the old percent form for the v1 check.
GNI is the WDI 'GNI (current US$)' value for the year, falling back to the latest earlier year
(2023, then 2022) when missing; gniShare is null if no GNI is available.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

FNAME = "10-remittance-corridors-vs-gni.js"
YEARS = [2021, 2024]
FIELDS = ["source", "recipient", "flow2021", "flow2024", "gniShare2021", "gniShare2024",
          "recipientRemitShare2021", "recipientRemitShare2024"]
GNI_FALLBACK = 2  # years back

_gni = None


def load_gni() -> pd.DataFrame:
    global _gni
    if _gni is None:
        g = pd.read_excel(common.GNI_CURRENT_USD, header=3)
        g.columns = [str(c) for c in g.columns]
        _gni = g.set_index("Country Code")
    return _gni


def gni_for(code: str, year: int):
    g = load_gni()
    if code not in g.index:
        return None
    for y in range(year, year - GNI_FALLBACK - 1, -1):
        v = g.at[code, str(y)]
        if pd.notna(v):
            return float(v)
    return None


def text_or_none(v):
    # Unclassified countries (e.g. VEN has no WB income group) -> null; the figure shows
    # 'Income status unavailable'.
    return v if isinstance(v, str) else None


def build(version: str, share_as_fraction: bool = True) -> dict:
    m = common.load_matrix(version)
    m = m[m["year"].isin(YEARS) & m["scored"]]
    by_year = {y: m[m["year"] == y].set_index(["s", "r"]) for y in YEARS}

    pairs = list(by_year[2021].index)
    seen = set(pairs)
    pairs += [p for p in by_year[2024].index if p not in seen]

    gni = {(c, y): gni_for(c, y) for y in YEARS for c in set(m["r"])}

    corridors = []
    for s, r in pairs:
        flows, gshare, rshare = [], [], []
        for y in YEARS:
            t = by_year[y]
            if (s, r) in t.index:
                row = t.loc[(s, r)]
                f = float(row["flow"])
                flows.append(float(round(f)))
                g = gni[(r, y)]
                gshare.append(round(f / g, 12) if g else None)
                pct = float(row["share_pct"])
                rshare.append(round(pct / 100, 14) if share_as_fraction else round(pct, 12))
            else:
                flows.append(None)
                gshare.append(None)
                rshare.append(None)
        corridors.append([s, r] + flows + gshare + rshare)

    conc = common.load_concordance().drop_duplicates("WB_A3").set_index("WB_A3")
    codes = {c for p in pairs for c in p}
    names = {}
    for code, nm in zip(m["r"], m["rname"]):
        names[code] = nm
    for code, nm in zip(m["s"], m["sname"]):
        names.setdefault(code, nm)
    countries = {}
    for code in sorted(codes, key=lambda c: names[c]):
        countries[code] = {
            "name": names[code],
            "region": text_or_none(conc.at[code, "WB region"]),
            "income": text_or_none(conc.at[code, "WB income group"]),
        }
    regions = sorted({v["region"] for v in countries.values() if isinstance(v["region"], str)})
    incomes = sorted({v["income"] for v in countries.values() if isinstance(v["income"], str)})
    return {"CGD_VIZ_DATA": {
        "fields": FIELDS,
        "countries": countries,
        "corridors": corridors,
        "summary": {"corridors": len(corridors), "countries": len(countries),
                    "regions": regions, "incomes": incomes},
    }}


def check(consts: dict):
    d = consts["CGD_VIZ_DATA"]
    for row in d["corridors"]:
        for v in row[2:]:
            assert v is None or math.isfinite(v), row
    for k, v in d["countries"].items():
        assert isinstance(v["name"], str) and isinstance(v["region"], str), (k, v)
        if v["income"] is None:
            print("    note: no WB income group for", k, v["name"])


if __name__ == "__main__":
    v1 = build("v1", share_as_fraction=False)
    check(v1)
    common.report("fig10", v1, common.load_existing(FNAME))
    v2 = build("v2")
    check(v2)
    print("staged", common.stage(FNAME, "v1", v1))  # percent form: byte-for-byte check against the committed file
    print("staged", common.stage(FNAME, "v2", v2))
    for v, c in (("v1", v1), ("v2", v2)):
        print(v, c["CGD_VIZ_DATA"]["summary"])
