# Bilateral remittances matrix update — interactive visualisations

This repository hosts the interactive visualisations accompanying the bilateral remittances matrix update.

The visualisations are static HTML files designed to be viewed directly through GitHub Pages or embedded in a digital note using iframes.

## Preview

A preview page with all visualisations embedded is available here:

https://samhuckstep.github.io/Bilateral-remittances-matrix-update/preview.html

## Individual visualisations

1. **Data coverage gaps in the bilateral remittance model**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/1-data-coverage-gaps.html

2. **Modelled remittances sent compared with World Bank payments data**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/2-model-v-wb.html

3. **Remittance inflows rose for most countries**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/3-total-remittance-flows.html

4. **The geography of remittance flows**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/4-remittances-map.html

5. **Remittance flows by source and recipient region**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/5-remittance-flows-regions.html

6. **Remittance flows by source and recipient income group**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/6-remittance-flows-incomes.html

7. **Access to productive emigration opportunities varies**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/7-migrant-stock-vs-gni.html

8. **How concentrated are recipient countries’ remittance sources?**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/8-remittances-source-dependence.html

9. **How important are remittance source countries to recipients?**
   https://samhuckstep.github.io/Bilateral-remittances-matrix-update/9-remittance-source-importance.html

10. **Remittances vs. ODA and FDI from OECD countries**
    https://samhuckstep.github.io/Bilateral-remittances-matrix-update/10-remittances-vs-oda-fdi.html

11. **Total remittance inflows relative to current US$ GNI, 2021–2024**
    https://samhuckstep.github.io/Bilateral-remittances-matrix-update/11-total-remittances-vs-gni.html

12. **Which remittance corridors matter most relative to recipient GNI?**
    https://samhuckstep.github.io/Bilateral-remittances-matrix-update/12-remittance-corridors-vs-gni.html

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

Production hosting must use an origin on the CGD resize listener's allowlist. At present that includes `https://center-for-global-development.github.io` and CGD Workers subdomains. The `samhuckstep.github.io` links above are useful for direct preview but will not resize inside the CGD parent unless communications explicitly adds that origin. Analytics and resize have separate allowlists and both must be checked after deployment.

The parent listener is already deployed on CGD and must not be copied into an individual visualisation. For local or same-origin preview, `preview.html` measures its child frames directly because a child correctly addressed to `https://www.cgdev.org` cannot resize a localhost parent.

Interaction events are documented in [TRACKING.md](TRACKING.md). Do not add a separate analytics tag inside an iframe.

## Notes

These visualisations are static HTML files. They are intended for public viewing and embedding through GitHub Pages.

The remittance estimates shown in the visualisations are modelled bilateral remittance-flow estimates. Values are generally shown in current US dollars unless otherwise stated in the notes to each visualisation.

## Maintainer

Sam Huckstep
