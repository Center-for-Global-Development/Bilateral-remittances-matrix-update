# Bilateral remittances matrix update — interactive visualisations

This repository hosts the interactive visualisations accompanying the bilateral remittances matrix update.

The visualisations are static HTML files designed to be viewed directly through GitHub Pages or embedded in a digital note using iframes.

## Preview

A preview page with all visualisations embedded is available here:

https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/preview.html

## Individual visualisations

1. **Data coverage gaps in the bilateral remittance model**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/1-data-coverage-gaps.html

2. **Modelled remittances sent compared with World Bank payments data**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/2-model-v-wb.html

3. **Remittance inflows rose for most countries**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/3-total-remittance-flows.html

4. **The geography of remittance flows**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/4-remittances-map.html

5. **Remittance flows by source and recipient region**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/5-remittance-flows-regions.html

6. **Remittance flows by source and recipient income group**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/6-remittance-flows-incomes.html

7. **Access to productive emigration opportunities varies**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/7-migrant-stock-vs-gni.html

8. **How concentrated are recipient countries’ remittance sources?**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/8-remittances-source-dependence.html

9. **How important are remittance source countries to recipients?**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/9-remittance-source-importance.html

10. **Remittances vs. ODA and FDI from OECD countries**
    https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/10-remittances-vs-oda-fdi.html

11. **Total remittance inflows relative to current US$ GNI, 2021–2024**
    https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/11-total-remittances-vs-gni.html

12. **Which remittance corridors matter most relative to recipient GNI?**
    https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/12-remittance-corridors-vs-gni.html

## Embedding

Each visualisation contains the standard CGD child-side resize and analytics code. Embed it with a full-width iframe whose initial height is only a loading placeholder:

```html
<iframe
  src="https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/1-data-coverage-gaps.html"
  title="Data coverage gaps in the bilateral remittance model"
  loading="lazy"
  scrolling="no"
  style="display:block;width:100%;height:600px;border:0"
>
</iframe>
```

The child reports its content height with `{ type: "cgd-iframe-resize", height }`; the CGD parent listener applies that height after validating the child origin. Do not tune a permanent fixed height. The iframe reports again after width changes, font loading, filter changes, dialogs, or other content reflow.

Production hosting must use an origin on the CGD resize listener's allowlist. This repository's organisational GitHub Pages origin, `https://center-for-global-development.github.io`, is approved. Analytics and resize have separate allowlists and both must be checked after deployment.

The parent listener is already deployed on CGD and must not be copied into an individual visualisation. The repository's `preview.html` contains a strict same-origin preview listener for resize and analytics messages, plus a direct-measurement fallback for local file viewing. Preview analytics are retained only in `window.CGDPreviewAnalytics`; they are not forwarded to production analytics.

Interaction events are documented in [TRACKING.md](TRACKING.md). Do not add a separate analytics tag inside an iframe.

## The shared layer

Every figure loads the same three files, in this order, before its own `<style>`:

| File | Owns |
|---|---|
| `shared/cgd-figure.css` | Tokens — colour, type scale, control sizing, readability floors — plus the figure frame, fullscreen button, notes and scroll cues |
| `shared/cgd-responsive.css` | Control behaviour on compact viewports; the override layer, so it uses `!important` deliberately |
| `shared/cgd-embed.js` | The iframe resize contract, analytics, the `CGD_READY` signal and scroll-cue behaviour. Loads **last** in `<body>` |

A figure's own `<style>` block is for that figure's marks and nothing else. **Do not add a `:root` block or re-declare a shared component inside a figure.** Before `cgd-figure.css` existed, all twelve figures carried their own copy of the token block and re-derived every size independently; the result was 56 distinct font sizes across the set, many of them 0.1px apart. One file is what stops that recurring.

Two floors are enforced rather than advisory, and `qa/audit.py` fails the build on either: no text below 10px, and editable inputs at 16px at every width so iOS does not zoom-jump on focus. The type scale is otherwise deliberately dense.

`shared/vendor/` holds figure 4's dependencies — d3 7.9.0, topojson-client 3.1.0 and the world-atlas 2.0.2 geometry — at exact versions. These were previously loaded from a CDN at unpinned major ranges (`d3@7`, `world-atlas@2`) with no integrity hashes, so an unreachable CDN meant no map at all and a new upstream release could change the figure without a commit here. Same-origin files remove both problems. The trade is that ~250KB gzipped of geometry now arrives over the reader's own connection rather than from a CDN edge; see "The map is still slow" below.

> `shared/cgd-responsive.css` began as a byte-identical copy of the file in the ODA cuts project. It has since diverged: axis text on compact viewports is 10.5px rather than 9.5px, and editable inputs are 16px at all widths rather than only below 520px. Both were `!important` rules that no figure could opt out of, and both put text below the readable floor. If the two projects are ever reconciled, those two changes belong in the ODA copy as well.

## Figure data

Each figure's data lives in `data/<figure-slug>.js`, not in its HTML. The HTML
loads it with a plain `<script src>` before the figure's own script, so the
figure still renders synchronously — there is no loading state and no change to
the `CGD_READY` contract.

Two payload shapes, matching how each figure already consumed its data:

- **JSON figures** (3, 4, 7, 8, 9, 11, 12) get `const CGD_VIZ_DATA = "…"` — the
  original JSON as an escaped string, still handed to `JSON.parse`. The parse
  path is therefore unchanged. The escaping costs 1.4% gzipped.
- **Object-literal figures** (1, 5, 6, 10) keep their original `const`
  declarations, moved verbatim. A top-level `const` in a classic script binds in
  the global lexical environment, so the figure script that runs afterwards still
  sees it.

The data files are generated. Do not hand-edit them; regenerate and re-run
`qa/audit.py`. Each carries a header naming its byte count and sha256.

**Why `<script src>` and not `fetch` of a `.json`.** `fetch` from a `file://`
origin is blocked by CORS, and this repository supports opening a figure straight
from disk. A classic `<script src>` works from both `file://` and `https`. The
same applies to the map's vendored geometry, which is `shared/vendor/…-50m.js`
rather than `.json` for exactly this reason — `d3.json` uses `fetch`, so the
`.json` form broke the map when the file was opened locally. `qa/audit.py` now
fails any runtime `fetch`, same-origin included.

### What this bought, measured

HTML dropped from 19.24MB to 490KB across the twelve figures — figure 9 from
4.73MB to 38KB. A one-line code change now produces a reviewable diff instead of
rewriting a multi-megabyte file.

Total bytes over the wire are essentially unchanged: the data moved, it did not
shrink. The gain is on a **redeploy**, when the code changes and the data does
not, measured on a 4x-CPU-throttled phone at ~1.6 Mbps with the versioned data
file cached and the HTML revalidated:

| Figure | Cold: KB / time to ready | After a redeploy: KB / time to ready |
|---|---|---|
| 9 — source importance | 1,051 KB / 5.7 s | 10 KB / **0.4 s** |
| 11 — total vs GNI | 664 KB / 3.7 s | 8 KB / **0.4 s** |
| 1 — coverage gaps | 69 KB / 0.7 s | 13 KB / **0.2 s** |
| 3 — total flows | 28 KB / 0.6 s | 8 KB / **0.3 s** |
| 4 — map | 1,117 KB / 13.0 s | 16 KB / **6.7 s** |

Bump the `?v=` token on a figure's data file only when that data changes; leave
it alone for code-only changes, or the caching benefit is lost.

### The map is still slow, and this is why

Figure 4 evaluates 5.38MB of script: 4.26MB of corridor data, 761KB of country
geometry, 280KB of d3. Profiling the compute on a throttled phone shows the cost
is *not* in any one algorithm — `JSON.parse` of the 3.56MB corridor payload is
102 ms, `topojson.feature` is 17 ms, fitting the projection 286 ms and building
all 241 country paths 510 ms, about 0.9 s in total. The remaining time is
evaluating those megabytes of script and building the SVG.

So the lever is payload size, which is a data-modelling decision rather than a
rendering one. Two options, neither taken here because both change what the
figure shows:

- The corridor payload carries all 17,130 flows; the default view draws 341.
  Serving a pre-ranked subset, with the long tail fetched on demand, would cut
  the bulk of that 4.26MB.
- The geometry is world-atlas at 1:50m. The 1:110m build is roughly a tenth the
  size and is ample at the rendered size, but visibly coarser once a reader zooms
  in.

## Verifying a change

`qa/audit.py` loads every figure in headless Chromium at 320 / 360 / 390 / 430 / 768 / 1200px, waits for that figure's own `window.CGD_READY`, and measures. There is no model in the loop — every check is a measurement, and it exits non-zero on any failure.

```bash
pip install playwright && python -m playwright install chromium
python qa/audit.py
```

```bash
python qa/audit.py 4 9 --shots qa/shots
```

It checks: boxes escaping the frame; control text clipped, or spilling outside its own control; SVG text clipped by a panel; overlapping axis and annotation text; overlapping control groups; tap targets below 24px; editable inputs below 16px; any text below 10px; a `<select>` showing a blank or unreadable value; bare stripes of unused control panel; horizontal page overflow; whether any marks rendered at all; console errors; and, statically, that no figure loads a third-party script or fetches from a third-party origin.

The focus check compares each control's computed style focused against unfocused and accepts **any** visible difference. These figures legitimately suppress the browser ring with `outline: none` and substitute a background tint, so insisting on an outline would report ~250 false failures. Measuring the difference instead found the one real gap: figure 10's legend toggles were styled `:focus-visible:not(.active)` while all three start active, so focusing one changed nothing.

It also fails a figure whose root is not `.viz-wrapper`. Most checks scope to that root, so a figure without it would pass by having nothing examined — which is exactly how figures 2 and 10 once came back clean.

[`.github/workflows/verify.yml`](.github/workflows/verify.yml) runs the same command on every push and pull request and uploads the screenshots, so a broken figure cannot merge.

The audit does not replace exercising state by hand: changing each filter and `All`, opening and closing a detail view, paging to the bounds, rotating with a dialog open, and confirming the iframe height both grows **and** shrinks.

## Notes

These visualisations are static HTML files. They are intended for public viewing and embedding through GitHub Pages.

The remittance estimates shown in the visualisations are modelled bilateral remittance-flow estimates. Values are generally shown in current US dollars unless otherwise stated in the notes to each visualisation. The two matrices (figures 5 and 6) print their cells in current US$ billions, declared on the display toggle, so that a column of cells can be compared by eye without decoding a per-cell magnitude suffix.

Text files are stored with LF endings (see `.gitattributes`). The repository previously held a mix, which made a two-line change to one of the CRLF figures look like a whole-file rewrite.

## Maintainer

Sam Huckstep
