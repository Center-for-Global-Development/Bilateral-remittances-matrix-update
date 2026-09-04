# CGD interactive analytics manifest

All 12 visualisations use the CGD iframe analytics contract:

- `interactive_view` is sent once after the child page loads.
- Meaningful controls send `interactive_engagement`.
- Production messages are flat objects sent only to `https://www.cgdev.org`.
- The organisational GitHub Pages preview is an explicit non-production exception: children use the exact referrer origin `https://center-for-global-development.github.io`, and `preview.html` validates and retains events locally without forwarding them to GA4.
- `interactive_name` is stable, unique, and kebab-case.
- `action_label` is stable and snake_case.

The shared implementation is `shared/cgd-embed.js`. Changes to tracked controls, names, or labels must update this manifest in the same commit.

`shared/cgd-embed.js` also carries the `CGD_READY` signal that `qa/audit.py` waits on, and the scroll-cue behaviour for regions wider than the panel. Neither sends analytics.

## Unchanged by the 2026-09 review pass

That pass altered control labels, layout and both shared stylesheets. It did **not** add, remove or rename a tracked control, and `action_value` is unaffected because it is read from each control's `data-*` attribute rather than its visible text. Verified in a listening parent:

| Figure | Control | Visible label | `action_value` |
|---|---|---|---|
| 5 | `#metricToggle` | `US$` → `$bn` | `usd` / `pct`, from `data-metric` |
| 6 | `#metricToggle` | `US$` → `$bn` | `usd` / `pct`, from `data-metric` |
| 4 | `#scopeToggle` | unchanged | `regional`, from `data-scope` |
| 12 | `#roleToggle` | unchanged | `source`, from `data-role` |

The same check confirmed `interactive_view` still fires exactly once per figure with the correct `interactive_name`, and that the reported height both grows and shrinks (`667 → 822 → 667` on figure 1's view toggle).

Two elements were removed in that pass; neither was ever tracked: figure 10's instructional subtitle, and figure 1's `No stock record` card, which restated a bar in its own chart.

## Event inventory

| File / `interactive_name` | Tracked engagements |
|---|---|
| `1-data-coverage-gaps.html` / `bilateral-remittances-data-coverage` | `filter/year`; `view_control/coverage_view`; `filter/corridor_limit`; `filter/country`; `filter/region`; `detail_open/country_detail`; `detail_open/corridor_detail`; `detail_close/country_detail`; `detail_close/corridor_detail`; `view_control/fullscreen` |
| `2-model-v-wb.html` / `bilateral-remittances-model-v-world-bank` | `filter/income_group`; `filter/country`; `filter/year`; `view_control/fullscreen` |
| `3-total-remittance-flows.html` / `bilateral-remittances-total-flows` | `filter/income_group`; `filter/country`; `filter/region`; `view_control/fullscreen` |
| `4-remittances-map.html` / `bilateral-remittances-map` | `view_control/flow_direction`; `filter/year`; `view_control/map_scope`; `filter/country`; `detail_open/country_detail`; `detail_open/corridor_detail`; matching `detail_close/country_detail` or `detail_close/corridor_detail`; `view_control/fullscreen` |
| `5-remittance-flows-regions.html` / `bilateral-remittances-regions-matrix` | `filter/year`; `view_control/metric`; `detail_open/matrix_cell`; `navigate/corridor_page`; `detail_close/matrix_cell`; `view_control/fullscreen` |
| `6-remittance-flows-incomes.html` / `bilateral-remittances-income-matrix` | `filter/year`; `view_control/metric`; `detail_open/matrix_cell`; `navigate/corridor_page`; `detail_close/matrix_cell`; `view_control/fullscreen` |
| `7-migrant-stock-vs-gni.html` / `bilateral-remittances-migrant-stock-gni` | `view_control/metric`; `filter/region`; `filter/country`; `filter/income_group`; `detail_open/country_detail`; `navigate/destination_page`; `detail_close/country_detail`; `view_control/fullscreen` |
| `8-remittances-source-dependence.html` / `bilateral-remittances-source-dependence` | `view_control/metric`; `filter/income_group`; `filter/country`; `filter/region`; `detail_open/country_detail`; `view_control/corridor_sort`; `detail_close/country_detail`; `view_control/fullscreen` |
| `9-remittance-source-importance.html` / `bilateral-remittances-source-importance` | `view_control/metric`; `filter/income_group`; `filter/country`; `filter/region`; `detail_open/country_detail`; `view_control/corridor_sort`; `detail_open/metric_definition`; `detail_close/metric_definition`; `detail_close/country_detail`; `view_control/fullscreen` |
| `10-remittances-vs-oda-fdi.html` / `bilateral-remittances-oda-fdi` | `filter/income_group`; `filter/country`; `view_control/country_role`; `view_control/comparison_mode`; `view_control/ranking_metric`; `navigate/previous_page`; `navigate/next_page`; `view_control/fullscreen` |
| `11-total-remittances-vs-gni.html` / `bilateral-remittances-total-gni` | `filter/income_group`; `filter/country`; `filter/region`; `view_control/fullscreen` |
| `12-remittance-corridors-vs-gni.html` / `bilateral-remittances-corridors-gni` | `view_control/country_role`; `filter/country`; `filter/corridor_limit`; `filter/region`; `navigate/previous_page`; `navigate/next_page`; `detail_close/corridor_detail`; `view_control/fullscreen` |

`action_value` is populated from the selected control value, its relevant `data-*` value, its accessible label, or its displayed text. It is omitted when no meaningful value exists.

## Deliberately not tracked

- Hover and tooltip display.
- Pointer movement, scrolling, resizing, and automatic re-rendering.
- Text typed while searching a country list; only a completed option selection is tracked.
- Map pan, wheel/pinch zoom, and the map zoom/reset buttons.
- Passive chart marks that do not open a discrete detail view.

These exclusions avoid inflating engagement with continuous, accidental, or low-signal behaviour.
