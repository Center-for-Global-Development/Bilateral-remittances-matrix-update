# Regenerating the figure data

The payloads in `data/` (and the two small data blocks still inline in HTML —
figure 8's `INCOME_BY_CODE` and figure 12's `rawData`) are generated from the
bilateral remittance matrix by the scripts in this folder. Do not hand-edit them.

| Script | Writes |
|---|---|
| `fig01_total_remittance_flows.py` | `data/1-total-remittance-flows.js` |
| `fig02_remittances_map.py` | `data/2-remittances-map.js`, `data/2-remittances-map-details.js` |
| `fig03_remittance_flows_regions.py` | `data/3-remittance-flows-regions.js` |
| `fig04_remittance_flows_incomes.py` | `data/4-remittance-flows-incomes.js` |
| `fig05_migrant_stock_vs_gni.py` | `data/5-migrant-stock-vs-gni.js` |
| `fig06_remittances_source_dependence.py` | `data/6-remittances-source-dependence.js` |
| `fig07_remittance_source_importance.py` | `data/7-remittance-source-importance.js` |
| `fig08_remittances_vs_oda_fdi.py` | `data/8-remittances-vs-oda-fdi.js` (+ `INCOME_BY_CODE` in the HTML) |
| `fig09_total_remittances_vs_gni.py` | `data/9-total-remittances-vs-gni.js` |
| `fig10_remittance_corridors_vs_gni.py` | `data/10-remittance-corridors-vs-gni.js` |
| `fig11_data_coverage_gaps.py` | `data/11-data-coverage-gaps.js` |
| `fig12_model_v_wb.py` | inline `rawData` in `12-model-v-wb.html` |

## Inputs

Paths are in `common.py`; the project folder defaults to the CGD OneDrive
location and can be overridden with `REMIT_PROJECT`.

* **Matrix, v2 (current):** the latest build in
  `2024 update/outputs/v2/` of the project folder (UN DESA 2020-release and
  national-data supplementation of omitted origins, Eurostat blanks treated as
  unpublished, missing-income rule). The published CSV
  (`Update blog/CGD updated 2024 bilateral remittances matrix.csv`) is this matrix
  rounded to ten significant figures.
* **Matrix, v1:** the full-precision May 2026 build the previously committed
  figures were made from. Used only to check the scripts.
* World Bank remittances received/paid and the concordance (source workbook),
  World Bank GNI in current US$ (`GNI current US$.xls`), and OECD ODA/FDI (the
  `Remittances - ODA - FDI` sheets) — non-model inputs.

A corridor counts as allocated if its status is `scored_allocated` or, from v2,
`scored_source_income_missing_floor` (`common.SCORED_STATUSES`).

## Running

```bash
# each script rebuilds its payload from v1 and reports mismatches against the
# committed file, then builds v2; both are staged in build/_staging/
python build/fig01_total_remittance_flows.py     # ... and so on for each figure

python build/write_data.py v1 --check            # optional: byte-level comparison
python build/write_data.py v2 --version-token YYYYMMDD
python qa/audit.py
```

`write_data.py` writes only files whose content changed and bumps the `?v=` token
on those, so a reader's cached copy of an unchanged payload stays valid.

## What the v1 check established (September 2026)

Every script rebuilds its committed payload from v1 with zero mismatches at a
relative tolerance of 1e-6 (most at 1e-9 or tighter; several byte-for-byte).
Deliberate differences in the v2 output, beyond the new numbers:

* Accented names (Curaçao, Côte d'Ivoire, …) were mis-encoded in figures 3, 4, 6,
  7 and 9. The v1 check reproduces the mis-encoding; v2 writes them correctly.
* Figure 10's recipient share is now stored as a fraction. The figure's
  `normalisePercentLike()` divides by 100 only above 1.5, so the percent form
  previously showed any share of 1.5% or less 100 times too large in the popup.
* Figure 7's corridor object is keyed in name order; the committed order looked
  like Python set iteration order and was not reproducible. The figure only looks
  corridors up by id.
* Figure 8's `STATS.rem` is summed from the matrix rather than from a
  15-significant-figure Excel copy (the figure does not read `STATS`).

Known limits of the v2 data, not code defects: Venezuela has no World Bank
income group, so its corridors appear under "All income groups" only (and are
outside figure 4's income grid); South Sudan and Yemen have no World Bank GNI in
current US$ after 2015 and 2018, so their corridors carry no GNI share and are
absent from figure 10.
