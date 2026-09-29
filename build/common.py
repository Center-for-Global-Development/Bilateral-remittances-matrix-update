"""
Shared helpers for regenerating the figure data payloads in data/.

Each build/figNN_*.py script turns the bilateral remittance matrix (plus the
auxiliary sheets it needs) into the object(s) a figure reads. It is checked by
rebuilding the committed payload from the v1 matrix, then run on the current
matrix. See build/README.md.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
PROJECT = Path(
    os.environ.get(
        "REMIT_PROJECT",
        r"C:\Users\SamuelHuckstep(shuck\OneDrive - Center for Global Development\Remittances\Bilateral remtitance matrix update",
    )
)
STAGING = Path(os.environ.get("REMIT_STAGING", str(REPO / "build" / "_staging")))

MATRIX_PATHS = {
    # v1: the matrix the committed figures were built from (as published in May/June 2026).
    # Full-precision v1 build output (the published CSV is rounded to ~10 significant figures,
    # and now holds v2; the rounded v1 copy is kept as "... - v1 (superseded).csv").
    "v1": PROJECT / "2024 update" / "outputs" / "remittance_matrix_combined_2021_2024_20260513_092121" / "matrix_long_2021_2024.csv",
    # v2: UN DESA 2020-release and national-data supplementation, Eurostat blanks, missing-income rule.
    "v2": None,  # resolved lazily: latest build in 2024 update/outputs/v2/
}
WORKBOOK = PROJECT / "2024 update" / "Sources for bilateral remittance matrix update v3.xlsx"
GNI_CURRENT_USD = PROJECT / "Update blog" / "Sheets for visualisations" / "GNI current US$.xls"
SHEETS_V2 = PROJECT / "Update blog" / "Sheets for visualisations" / "v2- Russia-Ukraine corridor blocked"

# Allocation statuses that count as a scored, allocated corridor. v2 adds the second.
SCORED_STATUSES = {"scored_allocated", "scored_source_income_missing_floor"}

SHORT_COLUMNS = {
    "Year": "year",
    "Recipient WB A3": "r",
    "Recipient country name": "rname",
    "Source WB A3": "s",
    "Source country name": "sname",
    "Bilateral remittances (current US$)": "flow",
    "Bilateral remittances share (% of recipient total)": "share_pct",
    "Total recipient remittances (current US$)": "rtotal",
    "Migrant stock in source country": "stock",
    "Ratha-Shaw income-based remittances score": "score",
    "Unnormalised allocation score": "corridor_score",
    "Recipient allocation score denominator": "denominator",
    "Allocation status": "status",
    "Stock data source": "stock_source",
    "Stock data release": "stock_release",
    "Stock data reference year": "stock_ref_year",
    "Migrant-stock record present?": "has_stock_record",
    "Source-reported zero migrant stock?": "reported_zero",
    "Self corridor?": "self",
    "Blocked corridor?": "blocked",
    "GNI, recipient (current international $)": "gni_r",
    "GNI year, recipient": "gni_r_year",
    "GNI lag status, recipient": "gni_r_lag",
    "GNI, source (current international $)": "gni_s",
    "GNI year, source": "gni_s_year",
    "GNI lag status, source": "gni_s_lag",
    "Partial migrant-stock coverage, recipient?": "partial_r",
    "Partial migrant-stock coverage, source?": "partial_s",
}


def matrix_path(version: str) -> Path:
    if version == "v2":
        builds = sorted((PROJECT / "2024 update" / "outputs" / "v2").glob("remittance_matrix_combined_*"))
        return builds[-1] / "matrix_long_2021_2024.csv"
    return MATRIX_PATHS[version]


def load_matrix(version: str, raw: bool = False) -> pd.DataFrame:
    """The long matrix. raw=True returns the published column names untouched."""
    df = pd.read_csv(matrix_path(version))
    if raw:
        return df
    df = df.rename(columns={k: v for k, v in SHORT_COLUMNS.items() if k in df.columns})
    df["scored"] = df["status"].isin(SCORED_STATUSES)
    return df


def load_concordance() -> pd.DataFrame:
    c = pd.read_excel(WORKBOOK, sheet_name="Data_concordance")
    c["WB_A3"] = c["WB_A3"].astype(str).str.strip()
    return c


def load_existing(fname: str) -> dict:
    """Decode a committed data/<fname> into {const_name: value}."""
    text = (REPO / "data" / fname).read_text(encoding="utf8")
    body = text[text.index("*/") + 2:].strip()
    out = {}
    dec = json.JSONDecoder()
    for m in re.finditer(r"const\s+(\w+)\s*=\s*", body):
        val, _ = dec.raw_decode(body[m.end():])
        if isinstance(val, str):
            val = json.loads(val)
        out[m.group(1)] = val
    return out


def compare(a, b, path="", rtol=1e-6, atol=1e-6, out=None, limit=25):
    """Recursive structural/numeric diff. Returns a list of (path, a, b) mismatches."""
    if out is None:
        out = []
    if len(out) >= limit * 20:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append((f"{path}.{k}", a.get(k, "<missing>"), b.get(k, "<missing>")))
            else:
                compare(a[k], b[k], f"{path}.{k}", rtol, atol, out, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((f"{path}[len]", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, f"{path}[{i}]", rtol, atol, out, limit)
    elif isinstance(a, bool) or isinstance(b, bool):
        if a != b:
            out.append((path, a, b))
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if (isinstance(a, float) and math.isnan(a)) and (isinstance(b, float) and math.isnan(b)):
            return out
        if not math.isclose(a, b, rel_tol=rtol, abs_tol=atol):
            out.append((path, a, b))
    elif a != b:
        out.append((path, a, b))
    return out


def report(name: str, rebuilt: dict, committed: dict, rtol=1e-6, atol=1e-6, show=25) -> int:
    diffs = compare(rebuilt, committed, rtol=rtol, atol=atol)
    print(f"[{name}] rebuilt-from-v1 vs committed: {len(diffs)} mismatches (rtol={rtol}, atol={atol})")
    for p, x, y in diffs[:show]:
        print(f"    {p}: rebuilt={str(x)[:100]!s}  committed={str(y)[:100]!s}")
    return len(diffs)


def stage(fname: str, version: str, consts: dict) -> Path:
    """Write the rebuilt object(s) for data/<fname> to the staging folder as JSON."""
    d = STAGING / version
    d.mkdir(parents=True, exist_ok=True)
    p = d / (fname + ".json")
    p.write_text(json.dumps(consts, ensure_ascii=False, allow_nan=False), encoding="utf8")
    return p
