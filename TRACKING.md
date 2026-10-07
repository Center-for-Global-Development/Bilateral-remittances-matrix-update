# Event Tracking: Bilateral remittances matrix update

Tracking implemented per [CGD Interactive Analytics Tracking Standard](https://github.com/Center-for-Global-Development/cgd-interactive-toolkit/blob/main/analytics-tracking-standard.md).

Twelve separately embedded figures, each with its own `interactive_name`. All of them share one implementation, `shared/cgd-embed.js`:

- `interactive_view` fires once per figure on load.
- Each figure's slug is set on its `<html>` element as `data-cgd-interactive-name`. The tracking rules are keyed on that slug, not on the filename, so renaming or renumbering a file does not affect tracking.
- `action_value` comes only from the value each rule declares, never from visible text or `aria-label`s. It is omitted when the rule declares none.
- Messages are flat objects sent to `https://www.cgdev.org`. The one exception is `preview.html` on the organisational GitHub Pages origin or on localhost, where the children post to the preview page itself, which keeps events in `window.CGDPreviewAnalytics` and never forwards them to GA4.

## Shared value sets

Every `action_value` is drawn from one of these bounded sets, or from the per-control values listed in the tables below.

| Set | Values |
|---|---|
| Country | ISO3 code (`AFG`, `IND`, …) or `ALL`, ~230 values |
| Region | `East Asia & Pacific`, `Europe & Central Asia`, `Latin America & Caribbean`, `Middle East & North Africa`, `North America`, `South Asia`, `Sub-Saharan Africa`, or `ALL` |
| Income group | `High income`, `Upper middle income`, `Lower middle income`, `Low income`, or `ALL` |
| Year | `2021`, `2024`; the two matrices also have `change` |
| Popup page | `prev`, `next` |

`view_control/fullscreen` appears in every figure, with no value.

## Tracked Events

### `bilateral-remittances-total-flows` — `1-total-remittance-flows.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `filter` | `income_group` | income group | Native select |
| `filter` | `country` | country | Combobox option |
| `filter` | `region` | region | Legend toggle |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-map` — `2-remittances-map.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `view_control` | `flow_direction` | `inflows`, `outflows` | |
| `filter` | `year` | year | |
| `view_control` | `map_scope` | `countries`, `regional` | |
| `filter` | `country` | country, or region in regional scope | Picker option |
| `detail_open` | `country_detail` | country | Click on a country shape |
| `detail_open` | `corridor_detail` | | Click on a flow. No value: ~10,800 corridors |
| `detail_close` | `country_detail` / `corridor_detail` | | Label matches whichever popup was open |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-regions-matrix` — `3-remittance-flows-regions.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `filter` | `year` | year | |
| `view_control` | `metric` | `usd`, `pct` | |
| `detail_open` | `matrix_cell` | `<source>><recipient>` region codes, e.g. `EAP>SAS` | 49 pairs of `EAP`, `ECA`, `LAC`, `MENA`, `NAC`, `SAS`, `SSA` |
| `navigate` | `corridor_page` | popup page | |
| `detail_close` | `matrix_cell` | | |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-income-matrix` — `4-remittance-flows-incomes.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `filter` | `year` | year | |
| `view_control` | `metric` | `usd`, `pct` | |
| `detail_open` | `matrix_cell` | `<source>><recipient>` income codes, e.g. `HIC>LIC` | 16 pairs of `HIC`, `UMC`, `LMC`, `LIC` |
| `navigate` | `corridor_page` | popup page | |
| `detail_close` | `matrix_cell` | | |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-migrant-stock-gni` — `5-migrant-stock-vs-gni.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `view_control` | `metric` | `gni`, `migration` | |
| `filter` | `region` | region | Native select |
| `filter` | `country` | country | Combobox option |
| `filter` | `income_group` | income group | Legend toggle |
| `detail_open` | `country_detail` | country | Click on a bubble |
| `navigate` | `destination_page` | popup page | |
| `detail_close` | `country_detail` | | |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-source-dependence` — `6-remittances-source-dependence.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `view_control` | `metric` | `top1`, `top3` | |
| `filter` | `income_group` | income group | Native select |
| `filter` | `country` | country | Combobox option |
| `filter` | `region` | region | Legend toggle |
| `detail_open` | `country_detail` | country | Click on a point |
| `view_control` | `corridor_sort` | `largest`, `change` | |
| `detail_close` | `country_detail` | | |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-source-importance` — `7-remittance-source-importance.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `view_control` | `metric` | `avg`, `top` | |
| `filter` | `income_group` | income group | Native select |
| `filter` | `country` | country | Combobox option |
| `filter` | `region` | region | Legend toggle |
| `detail_open` | `country_detail` | country | Click on a point |
| `view_control` | `corridor_sort` | `largest`, `change` | |
| `detail_open` | `metric_definition` | | Formula popup, opened from inside the country popup |
| `detail_close` | `metric_definition` | | |
| `detail_close` | `country_detail` | | |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-oda-fdi` — `8-remittances-vs-oda-fdi.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `filter` | `income_group` | income group | Native select |
| `filter` | `country` | country | Listbox option |
| `view_control` | `country_role` | `recipient`, `source` | |
| `view_control` | `comparison_mode` | `2021`, `2024`, `change` | |
| `view_control` | `ranking_metric` | `all`, `rem`, `oda`, `fdi` | Legend toggles |
| `navigate` | `previous_page` | | |
| `navigate` | `next_page` | | |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-total-gni` — `9-total-remittances-vs-gni.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `filter` | `income_group` | income group | Native select |
| `filter` | `country` | country | Combobox option |
| `filter` | `region` | region | Legend toggle |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-corridors-gni` — `10-remittance-corridors-vs-gni.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `view_control` | `country_role` | `recipient`, `source` | |
| `filter` | `country` | country | Combobox option |
| `filter` | `corridor_limit` | `15`, `25`, `40`, `80` | |
| `filter` | `region` | region | Region pill toggle |
| `navigate` | `previous_page` | | |
| `navigate` | `next_page` | | |
| `detail_close` | `corridor_detail` | | |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-data-coverage` — `11-data-coverage-gaps.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `filter` | `year` | year | |
| `view_control` | `coverage_view` | `global`, `countries` | |
| `filter` | `corridor_limit` | `20`, `40`, `80`, `ALL` | |
| `filter` | `country` | country | Combobox option |
| `filter` | `region` | region | Legend toggle |
| `detail_open` | `country_detail` | country | Click on a bar |
| `detail_open` | `corridor_detail` | gap status: `no_stock_record_zero_allocation`, `recipient_unallocated_no_positive_usable_score`, `source_reported_zero_stock`, `unscored_missing_recipient_and_source_income`, `unscored_missing_recipient_income` | "See missing corridors" |
| `detail_close` | `country_detail` | | |
| `detail_close` | `corridor_detail` | | |
| `view_control` | `fullscreen` | | |

### `bilateral-remittances-model-v-world-bank` — `12-model-v-wb.html`

| `action_type` | `action_label` | `action_value` | Notes |
|---|---|---|---|
| `filter` | `income_group` | income group | Combobox option |
| `filter` | `country` | country | Combobox option |
| `filter` | `year` | year | |
| `view_control` | `fullscreen` | | |

## Not Tracked

- Hover and tooltip display: high volume, low signal.
- Map pan, wheel/pinch zoom, and the map zoom/reset buttons: continuous gestures.
- Text typed into a country search box. Only a completed option selection is tracked.
- Pointer movement, scrolling, resizing and automatic re-rendering.
- Chart marks that do not open a discrete detail view.

## Maintenance

Any change that adds, removes or renames a tracked control, or changes the values it sends, must update this file in the same commit.
