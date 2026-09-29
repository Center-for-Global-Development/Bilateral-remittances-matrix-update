# Bilateral remittances matrix update — interactive visualisations

This repository hosts the interactive visualisations accompanying the bilateral remittances matrix update.

The visualisations are static HTML files designed to be viewed directly through GitHub Pages or embedded in a digital note using iframes.

## Preview

A preview page with all visualisations embedded is available here:

https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/preview.html

## Individual visualisations

The numbering follows the running order of *The Geography of Remittances: An
Updated Global Bilateral Remittances Matrix*. Figures 11 and 12 — the two model
diagnostics — sit at the end of the note, after the substantive findings, and
were renumbered from 1 and 2 to match it.

1. **Remittance inflows rose for most countries**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/1-total-remittance-flows.html

2. **The geography of remittance flows**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/2-remittances-map.html

3. **Remittance flows by source and recipient region**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/3-remittance-flows-regions.html

4. **Remittance flows by source and recipient income group**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/4-remittance-flows-incomes.html

5. **Access to productive emigration opportunities varies**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/5-migrant-stock-vs-gni.html

6. **How concentrated are recipient countries’ remittance sources?**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/6-remittances-source-dependence.html

7. **How important are remittance source countries to recipients?**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/7-remittance-source-importance.html

8. **Remittances vs. ODA and FDI from OECD countries**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/8-remittances-vs-oda-fdi.html

9. **Total remittance inflows relative to current US$ GNI, 2021–2024**
   https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/9-total-remittances-vs-gni.html

10. **Which remittance corridors matter most relative to recipient GNI?**
    https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/10-remittance-corridors-vs-gni.html

11. **Data coverage gaps in the bilateral remittance model**
    https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/11-data-coverage-gaps.html

12. **Modelled remittances sent compared with World Bank payments data**
    https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/12-model-v-wb.html

The analytics slug in each file's `data-cgd-interactive-name` is unchanged and
carries no number, so the renumbering does not break event continuity. The
published URLs *do* change; anything already embedding these files needs its
`src` updated.

## Embedding

Each visualisation contains the standard CGD child-side resize and analytics code. Embed it with a full-width iframe whose initial height is only a loading placeholder:

```html
<iframe
  src="https://center-for-global-development.github.io/Bilateral-remittances-matrix-update/1-total-remittance-flows.html"
  title="Remittance inflows rose for most countries"
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
| `shared/cgd-figure.css` | Tokens — colour, type scale, control sizing, readability floors — plus the figure frame, fullscreen button, headline stats, notes and scroll cues |
| `shared/cgd-responsive.css` | Control behaviour on compact viewports; the override layer, so it uses `!important` deliberately |
| `shared/cgd-embed.js` | The iframe resize contract, analytics, the `CGD_READY` signal and scroll-cue behaviour. Loads **last** in `<body>` |

A figure's own `<style>` block is for that figure's marks and nothing else. **Do not add a `:root` block or re-declare a shared component inside a figure.** Before `cgd-figure.css` existed, all twelve figures carried their own copy of the token block and re-derived every size independently; the result was 56 distinct font sizes across the set, many of them 0.1px apart. One file is what stops that recurring.

Two floors are enforced rather than advisory, and `qa/audit.py` fails the build on either: no text below 10px, and editable inputs at 16px at every width so iOS does not zoom-jump on focus. The type scale is otherwise deliberately dense.

`shared/vendor/` holds the map's (figure 2) dependencies — d3 7.9.0, topojson-client 3.1.0 and the world-atlas 2.0.2 geometry — at exact versions. These were previously loaded from a CDN at unpinned major ranges (`d3@7`, `world-atlas@2`) with no integrity hashes, so an unreachable CDN meant no map at all and a new upstream release could change the figure without a commit here. Same-origin files remove both problems. The trade is that ~250KB gzipped of geometry now arrives over the reader's own connection rather than from a CDN edge; see "The map: what was done about its weight" below.

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

The map (figure 2) has a second file, `data/2-remittances-map-details.js`, holding the
per-corridor statistics its popups need. It is *not* loaded up front — see "The
map" below.

The data files are generated. Do not hand-edit them; regenerate them with the
scripts in [`build/`](build/README.md) and re-run `qa/audit.py`. Each carries a
header naming its byte count and sha256.

**Why `<script src>` and not `fetch` of a `.json`.** `fetch` from a `file://`
origin is blocked by CORS, and this repository supports opening a figure straight
from disk. A classic `<script src>` works from both `file://` and `https`. The
same applies to the map's vendored geometry, which is `shared/vendor/…-50m.js`
rather than `.json` for exactly this reason — `d3.json` uses `fetch`, so the
`.json` form broke the map when the file was opened locally. `qa/audit.py` now
fails any runtime `fetch`, same-origin included.

### What this bought, measured

HTML dropped from 19.24MB to 490KB across the twelve figures — source importance (figure 7) from
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

### The map: what was done about its weight, and what is left

The map loaded 5.38MB of script before it could draw. 2.78MB of that — 78% of
its data payload — was `flowStats`: per-year shares, migrant stocks and GNI
figures for 8,664 corridor pairs, read only by `safeStat()` to fill the corridor
and country popups. None of it is needed to draw the map, and most readers never
open a popup.

It now lives in `data/4-remittances-map-details.js`, injected after the map has
rendered:

- the injection waits for `cgd:ready`, not for `init()`. Parsing 3.3MB blocks the
  main thread, and an idle callback landing before the shared embed script has
  finished measuring pushed time-to-ready out by a second even though the map was
  already on screen;
- the two popup entry points go through `withDetails()`, so a click before the
  statistics arrive waits for them rather than showing zeros. Verified by
  clicking the instant the map became ready on a 400 Kbps link: the popup showed
  the same numbers, byte-identical to the fully-loaded case;
- the hover tooltip needed no change — it already guarded `st.p == null` and
  simply omits its "% of recipient total" line until the statistics land.

Measured on the throttled phone profile: **critical path 5.38MB → 2.12MB
(1,134KB → 516KB gzipped), transfer before the map appears 1,120KB → 515KB, time
to ready 13.0s → 9.9s.** No visual change, and all 108 render fingerprints stayed
identical.

> These measurements predate the September 2026 model update. The v2 matrix
> allocates more corridors, so the map now carries 10,784 corridor pairs rather
> than 8,664: `data/2-remittances-map.js` is 1.22MB (189KB gzipped) and
> `data/2-remittances-map-details.js` 4.06MB (731KB gzipped). The split and the
> deferred injection work exactly as described; only the byte counts moved.

What is left is CPU rather than network: evaluating d3 (280KB), the geometry
(761KB) and the map data (993KB), then fitting the projection (286 ms) and
building 241 country paths (510 ms).

**Do not swap the geometry for world-atlas 1:110m to save that 761KB.** It is
6× smaller gzipped and the temptation is obvious, but it carries 175 country ids
against the 50m build's 236. It would stop drawing 44 territories, 34 of them
with remittance corridors in the data — Samoa, Tonga, Comoros, Cape Verde,
Maldives, Micronesia, Kiribati, Marshall Islands, Mauritius, Bermuda, Aruba,
Curaçao among them. Those small states are precisely where remittance dependence
is highest, so the saving would cost the figure its subject.

The remaining option, not taken here, is topology-preserving simplification of
the 1:50m build (mapshaper, or `topojson-simplify`), which keeps all 236
territories and thins coordinate density instead of dropping places. That needs a
Node build step and a visual check at full zoom.

### Control sizing

Every control in the set renders at one height, `--cgd-control-min` (34px), set
in `shared/cgd-responsive.css`. Before that, the shared layer said
`height: auto`, so each control's height came from its own font-size and
padding: a segmented toggle was 42px, a search input 42px, a native select 36px,
a country trigger 34px, the migrant-stock figure's combo input 34.4px. Nine of the twelve figures
had two or three different heights sitting side by side.

Two things follow from that, and both matter if you touch this:

- a segmented pill bank is 34px *overall*, so its buttons are
  `--cgd-control-inner` (26px) — the bank's own 3px padding and 1px border make up
  the difference. That value is a token because it is set in two places, the base
  rule and the compact override, and they had drifted apart;
- a three-option toggle below 400px wraps to two rows instead of shrinking its
  labels, so it is legitimately taller. `qa/audit.py` checks that controls in one
  bank share a height and exempts a wrapped bank.

Native selects do not set `appearance: none` and draw no chevron of their own, so
they must not reserve padding for one — 30px of right padding was what truncated
the total-inflows figure's income filter to "All income g". They now take the width their widest
option needs above 600px, and one control per row below 420px, where half a bank
is narrower than a 16px-text label. The audit fails any select whose selected
option does not fit.

### Headline stats

Five figures open with a strip of headline numbers. They arrived with three
class vocabularies — `.kpi` in the coverage-gaps and ODA/FDI figures,
`.descriptor-tab` in the map and the corridors-vs-GNI figure, `.remit-card` in
the model-vs-World-Bank figure — because they were built at different times.
`.remit-card` has been folded into `.kpi`; the remaining two are both styled in
one place, under *headline stats* in `shared/cgd-figure.css`, and no figure
restates any of it.

They used to be cards: a bordered, rounded white box per number with a 3px
coloured bar across the top, driven by an inline `--accent`. The trim carried no
information — in the ODA/FDI figure the three accents repeated the series colours
already in the legend directly beneath, and elsewhere they mapped to nothing at
all — while three or four boxed panels competed for attention with the chart they
were meant to introduce. What is there now is the label, the number, its
qualifier, and one hairline separating the strip from the controls below it. The
`--accent` plumbing is gone from the render functions, and `.kpi::before` /
`.descriptor-tab::before` are neutralised in the shared file so a stray accent
does nothing.

The label is sentence case at the note size. A first pass set it uppercase at
10px with 0.07em tracking, which shouts for a label whose whole job is to stay
out of the number's way; quiet weight and colour do the separating instead.

Stats size to their own content and wrap, so the strip takes any number of them
and stacks cleanly on a phone without a per-figure column count.

### The matrices' corner cell

The two matrices (figures 3 and 4) used to label their axes with a corner box
split by a diagonal rule, "Source …" pinned above it and "Recipient …" below.
It made the reader decode a small diagram before reading the matrix. The corner
now simply labels the column it sits above — the row headers — and the source
axis is named once, in a quiet banner spanning the columns it belongs to.

The banner is emitted as three grid items (a sticky spacer, the banner with an
inline `grid-column: span N` from `groups.length`, a spacer) rather than one
explicitly placed item, so grid auto-placement still fills the rest of the
matrix row by row. The left spacer is sticky and opaque for the same reason the
corner is: without it the banner slides visibly under the frozen first column
when the matrix is scrolled sideways.

Row labels in the income matrix were left-aligned while its `Total` row, which
inherits `.total-header`, was centred. All of them are centred now, matching the
region matrix.

### The coverage-gaps figure's Year and View toggles

Both are two-option toggles whose width belongs to their labels. They were sized
with a percentage flex-basis inside a control bank that is itself
`width: fit-content` — circular, so each toggle settled on its floor and
ellipsised "Global" and "Countries" even at 1200px, with spare panel sitting to
the right of the bank. Above 601px each group is now `width: max-content` with
`flex-shrink` left at 1: `fit-content` measures the real labels, and the
button-level ellipsis stays as the last resort when the row is genuinely tight.
Below 601px `cgd-responsive.css` lays the bank out as a grid and none of it
applies.

Note that `qa/audit.py` passed the truncated version. Its clipped-text check
covers SVG text and native selects, not a `text-overflow: ellipsis` on a button
label; if that class of defect recurs, that is the check to extend.

### Selecting and deselecting a bar

The coverage-gaps figure's `.focus-ring` fired on `:hover` as well as `:focus`,
which drew a 1px box around every bar the pointer crossed on top of the tooltip
already naming it, and stayed drawn around a selected bar afterwards — it read
as a stuck hover state. The ring is now `:focus-visible` only, so it is purely a
keyboard affordance; a selected column is marked by the tick above it. No other
figure in the set drew a hover outline on a mark.

Selection also had no way out from the chart. Clicking the selected column
again, clicking the space around the columns, or pressing Escape now all return
to every recipient. And "All countries" in the Recipient box used to sit in the
same list as the recipients, so it was filtered out by whatever was in the
input — once a country was chosen, reopening the menu showed that country alone
and the way back had disappeared. It is pinned above the matches now, whatever
has been typed.

### Editable inputs and the 16px floor

`cgd-responsive.css` pinned every editable input to 16px at every width. That
floor exists to stop iOS zooming the page when a text field is focused, which
cannot happen with a mouse, and it had one visible cost: a combobox input sat at
16px beside a native select at 14px in the same bank, so the coverage-gaps
figure's "Recipient" box read noticeably larger than "Countries shown" next to
it. The floor is now conditioned on `(pointer: coarse)`.

That changed what the audit can assert, so the audit changed with it.
`qa/audit.py` now opens the phone widths (≤430px) with Playwright's touch
emulation on, which makes `(pointer: coarse)` match — so the 16px floor is
genuinely exercised rather than merely asserted against a headless mouse. At
768px and 1200px it checks the opposite property instead: that every editable
input matches the other controls in its bank.

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

It also checks that controls in one bank share a height, and that a `<select>`'s selected option actually fits — the two things behind the ragged control rows and the total-inflows figure's "All income g".

The focus check compares each control's computed style focused against unfocused and accepts **any** visible difference. These figures legitimately suppress the browser ring with `outline: none` and substitute a background tint, so insisting on an outline would report ~250 false failures. Measuring the difference instead found the one real gap: the ODA/FDI figure's legend toggles were styled `:focus-visible:not(.active)` while all three start active, so focusing one changed nothing.

It also fails a figure whose root is not `.viz-wrapper`. Most checks scope to that root, so a figure without it would pass by having nothing examined — which is exactly how the model-vs-World-Bank and ODA/FDI figures once came back clean.

[`.github/workflows/verify.yml`](.github/workflows/verify.yml) runs the same command on every push and pull request and uploads the screenshots, so a broken figure cannot merge.

The audit does not replace exercising state by hand: changing each filter and `All`, opening and closing a detail view, paging to the bounds, rotating with a dialog open, and confirming the iframe height both grows **and** shrinks.

## Notes

These visualisations are static HTML files. They are intended for public viewing and embedding through GitHub Pages.

The remittance estimates shown in the visualisations are modelled bilateral remittance-flow estimates. Values are generally shown in current US dollars unless otherwise stated in the notes to each visualisation. The two matrices (figures 5 and 6) print their cells in current US$ billions, declared on the display toggle, so that a column of cells can be compared by eye without decoding a per-cell magnitude suffix.

Text files are stored with LF endings (see `.gitattributes`). The repository previously held a mix, which made a two-line change to one of the CRLF figures look like a whole-file rewrite.

The map's "% of recipient total" is printed by `sharePct()`, which sets its decimal places from the magnitude of the value rather than using a fixed one. `flowStats.p` is already a percentage (exactly `v / rt * 100`), and the shares run from 0.000008% to 97.8%, so one decimal place rendered 43% of corridor-years as "0.0%" — 39% of India's corridors, for instance, whose contributions to large recipients are genuinely small but not zero. The rule gives about two significant figures throughout, and a share below a thousandth of a percent is printed as `<0.001%` rather than as a rounded-away zero. Do not pass these values through `pct()`, which multiplies by 100.

## Maintainer

Sam Huckstep
