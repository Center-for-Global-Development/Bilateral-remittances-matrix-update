"""
Write staged payloads (build/_staging/<version>/<fname>.json) into data/<fname>,
reproducing the committed serialisation, and bump the ?v= token in the HTML
that loads each changed file.

    python build/write_data.py v2 --version-token 20260929
    python build/write_data.py v1 --check      # rebuild from v1 and confirm bodies are byte-identical

Serialisation (matches the files previously committed):
  * Numbers are first rounded to common.SIG_FIGS significant figures, except in
    the files listed in common.FULL_PRECISION.
  * JSON-string payloads: the payload is compact JSON (separators ",", ":",
    non-ASCII kept) held in a JS string literal escaped with json.dumps
    defaults (ASCII escapes), then handed to JSON.parse by the figure.
  * Object-literal payloads: `const NAME = <compact JSON>;` per constant,
    one per line.
The header records the byte count and sha256 (first 32 hex characters) of the
body text that follows it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

# fname -> (kind, html file that loads it)
FILES = {
    "1-total-remittance-flows.js": ("json", "1-total-remittance-flows.html"),
    "2-remittances-map.js": ("json-map", "2-remittances-map.html"),
    "2-remittances-map-details.js": ("json-details", "2-remittances-map.html"),
    "3-remittance-flows-regions.js": ("literal", "3-remittance-flows-regions.html"),
    "4-remittance-flows-incomes.js": ("literal", "4-remittance-flows-incomes.html"),
    "5-migrant-stock-vs-gni.js": ("json", "5-migrant-stock-vs-gni.html"),
    "6-remittances-source-dependence.js": ("json", "6-remittances-source-dependence.html"),
    "7-remittance-source-importance.js": ("json", "7-remittance-source-importance.html"),
    "8-remittances-vs-oda-fdi.js": ("literal", "8-remittances-vs-oda-fdi.html"),
    "9-total-remittances-vs-gni.js": ("json", "9-total-remittances-vs-gni.html"),
    "10-remittance-corridors-vs-gni.js": ("json", "10-remittance-corridors-vs-gni.html"),
    "11-data-coverage-gaps.js": ("literal", "11-data-coverage-gaps.html"),
    # Figure 12 keeps its data inline in the HTML, as `const rawData = [...]`; only that array is replaced.
    "12-model-v-wb.js": ("inline-html", "12-model-v-wb.html"),
}


def compact(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def body_for(kind: str, consts: dict) -> str:
    if kind.startswith("json"):
        (name, value), = consts.items()
        return f"const {name} = {json.dumps(compact(value))};\n"
    return "".join(f"const {name} = {compact(value)};\n" for name, value in consts.items())


def header_for(fname: str, kind: str, consts: dict, body: str) -> str:
    slug = fname[:-3]
    raw = body.encode("utf8")
    size, digest = f"{len(raw):,}", hashlib.sha256(raw).hexdigest()[:32]
    if kind == "json-details":
        pairs = len(next(iter(consts.values())))
        return (
            f"/* Per-corridor detail statistics for {slug.replace('-details', '')}.\n *\n"
            f" * Generated, not hand-edited. See README.md, \"Figure data\" and build/README.md.\n"
            f" * {size} bytes, {pairs:,} corridor pairs, sha256 {digest}.\n"
            " * Read only by the corridor and country popups, so it is injected\n"
            " * after the map has drawn rather than blocking the first render.\n */\n"
        )
    if kind == "json-map":
        return (
            f"/* Map and corridor data for {slug}.\n *\n"
            f" * Generated, not hand-edited. See README.md, \"Figure data\" and build/README.md.\n"
            f" * {size} bytes, sha256 {digest}.\n"
            " * Everything needed to draw the map. The per-corridor detail\n"
            f" * statistics live in {slug}-details.js, loaded after render.\n */\n"
        )
    lead = (
        f"/* Data payload for {slug}.\n *\n"
        " * Generated, not hand-edited, by build/ from the bilateral remittance\n"
        " * matrix. See README.md, \"Figure data\", and build/README.md.\n *\n"
    )
    if kind == "json":
        return lead + (
            f" * JSON payload, {size} bytes, sha256 {digest}.\n"
            " * Handed to JSON.parse by the figure.\n */\n"
        )
    names = ", ".join(consts)
    return lead + (
        f" * {len(consts)} object-literal declaration(s) ({names}), {size} bytes, sha256 {digest}.\n"
        " * A top-level const in a classic script is visible to the figure\n"
        " * script that runs after it.\n */\n"
    )


INLINE_RE = re.compile(r"(const rawData = )(\[.*?\]);\n", re.S)


def inline_array(html_text: str) -> str:
    m = INLINE_RE.search(html_text)
    assert m, "inline rawData array not found"
    return m.group(2)


INCOME_RE = re.compile(r"(const INCOME_BY_CODE = )(\{.*?\});")


def fig8_income_map(consts: dict) -> str:
    """Figure 8 keeps a code -> WB income group map inline; regenerate it for the countries in the payload."""
    inc = common.load_concordance().drop_duplicates("WB_A3").set_index("WB_A3")["WB income group"]
    codes = sorted(c["code"] for c in consts["EMBED"]["countries"] if c["code"] != "ALL")
    return compact({c: inc[c] for c in codes if c in inc.index and isinstance(inc[c], str)})


def update_fig8_income(consts: dict, check: bool) -> bool:
    hp = common.REPO / "8-remittances-vs-oda-fdi.html"
    h = hp.read_text(encoding="utf8")
    old, new = INCOME_RE.search(h).group(2), fig8_income_map(consts)
    if check or old == new:
        return old == new
    hp.write_text(INCOME_RE.sub(lambda m: m.group(1) + new + ";", h, count=1), encoding="utf8", newline="\n")
    print("        regenerated INCOME_BY_CODE in 8-remittances-vs-oda-fdi.html")
    return False


def committed_body(fname: str) -> str:
    text = (common.REPO / "data" / fname).read_text(encoding="utf8")
    return text[text.index("*/") + 2:].lstrip("\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("version", choices=["v1", "v2"])
    ap.add_argument("--check", action="store_true", help="compare bodies with the committed files; write nothing")
    ap.add_argument("--version-token", default=None, help="new ?v= token for changed data files")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()

    failures = 0
    for fname in args.files or FILES:
        kind, html = FILES[fname]
        staged = common.STAGING / args.version / (fname + ".json")
        if not staged.exists():
            print(f"[skip] {fname}: nothing staged at {staged}")
            continue
        consts = json.loads(staged.read_text(encoding="utf8"))
        if kind == "inline-html":
            hp = common.REPO / html
            h = hp.read_text(encoding="utf8")
            new_arr, old_arr = compact(consts["rawData"]), inline_array(h)
            if args.check:
                failures += new_arr != old_arr
                print(f"[{'ok' if new_arr == old_arr else 'DIFF'}] {fname} (inline in {html})")
            elif new_arr == old_arr:
                print(f"[same] {fname} (inline in {html}): unchanged")
            else:
                hp.write_text(INLINE_RE.sub(lambda m: m.group(1) + new_arr + ";\n", h, count=1), encoding="utf8", newline="\n")
                print(f"[wrote] inline rawData in {html}")
            continue
        # Numbers go to data/ at common.SIG_FIGS significant figures, except the files in
        # common.FULL_PRECISION. The inline figure 12 array and figure 8's INCOME_BY_CODE
        # are not rounded.
        if fname not in common.FULL_PRECISION:
            consts = common.round_sig(consts)
        body = body_for(kind, consts)
        old = committed_body(fname)
        if fname.startswith("8-"):
            same_income = update_fig8_income(consts, args.check)
            if args.check:
                failures += not same_income
                print(f"[{'ok' if same_income else 'DIFF'}] INCOME_BY_CODE in 8-remittances-vs-oda-fdi.html")
        if args.check:
            same = body == old
            failures += not same
            print(f"[{'ok' if same else 'DIFF'}] {fname}: rebuilt body {'identical to' if same else 'differs from'} committed")
            continue
        if body == old:
            print(f"[same] {fname}: unchanged, left alone")
            continue
        (common.REPO / "data" / fname).write_text(header_for(fname, kind, consts, body) + body, encoding="utf8", newline="\n")
        print(f"[wrote] {fname}: {len(body.encode('utf8')):,} bytes (was {len(old.encode('utf8')):,})")
        if args.version_token:
            hp = common.REPO / html
            h = hp.read_text(encoding="utf8")
            h2 = re.sub(rf"(data/{re.escape(fname)}\?v=)\w+", rf"\g<1>{args.version_token}", h)
            if h2 != h:
                hp.write_text(h2, encoding="utf8", newline="\n")
                print(f"        bumped ?v= in {html}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
