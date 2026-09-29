"""Figure 4: allocated bilateral flows by source x recipient World Bank income group
(data/4-remittance-flows-incomes.js). Same builder as figure 3 (see its docstring), plus
the 2021->2024 change popups; globalTotals are written at 15 significant figures.
"""
from __future__ import annotations

import common
from fig03_remittance_flows_regions import build_group_matrix, summarise

FNAME = "4-remittance-flows-incomes.js"
INCOME_GROUPS = [
    ("HIC", "High income"), ("UMC", "Upper middle income"),
    ("LMC", "Lower middle income"), ("LIC", "Low income"),
]


def build(version: str) -> dict:
    return {"vizData": build_group_matrix(version, INCOME_GROUPS, "WB income group",
                                          with_change=True, global_g15=True)}


if __name__ == "__main__":
    v1 = build("v1")
    common.report("fig04", v1, common.load_existing(FNAME), rtol=1e-9, atol=1e-6)
    v2 = build("v2")
    common.stage(FNAME, "v1", v1)
    common.stage(FNAME, "v2", v2)
    summarise("fig04", v1, v2)
    for k in ("change|LIC|LIC", "change|LMC|HIC"):
        print(f"  {k} totalCount v1={v1['vizData']['changeTopCorridors'][k]['totalCount']} "
              f"v2={v2['vizData']['changeTopCorridors'][k]['totalCount']}")
