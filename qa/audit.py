#!/usr/bin/env python3
"""Deterministic render audit for the bilateral remittances figures.

Serves the repository, loads every figure at phone, tablet and desktop widths,
waits for the figure's own `window.CGD_READY` signal, and runs a set of layout,
type-scale and accessibility checks in the page. Exits non-zero on any failure so
a broken figure cannot merge.

There is no model in the loop: every check below is a measurement.

    python qa/audit.py                  # all figures, all widths
    python qa/audit.py 3 9              # only figures 3 and 9
    python qa/audit.py --shots qa/shots # also write full-page screenshots

Requires: pip install playwright && python -m playwright install chromium
"""
import argparse
import functools
import glob
import http.server
import json
import os
import re
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8842
WIDTHS = (320, 360, 390, 430, 768, 1200)

# House type scale (see README). These are floors, not suggestions: the CGD
# figures are deliberately dense, but text below the note size is not readable
# on a phone and 16px on editable inputs is what stops iOS zoom-jumping.
MIN_TEXT_PX = 10.0
MIN_INPUT_PX = 16.0
MIN_TAP_PX = 24

# What counts as "this figure drew something". Several figures draw their marks
# as DOM elements rather than SVG (the matrices use .cell, figure 10 stacks
# .combo-bar divs), so the selector has to cover both.
MARK_SELECTOR = ('svg circle, svg rect, svg path.series, svg path.country, '
                 'svg line.connector, .cell, .bar-col, .combo-bar, '
                 '.country-row, .corridor-row')


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


AUDIT = r"""(cfg)=>{
 const bad=[];
 const shown=n=>{const cs=getComputedStyle(n);
   return cs.display!=='none'&&cs.visibility!=='hidden'&&n.getClientRects().length>0;};
 const scrollableAncestor=n=>{for(let p=n.parentElement;p&&p!==document.body;p=p.parentElement){
   const o=getComputedStyle(p);if(/auto|scroll/.test(o.overflowX)||/auto|scroll/.test(o.overflow))return true;}
   return false;};
 const clipAncestor=n=>{for(let p=(n.ownerSVGElement||n).parentElement;p&&p!==document.body;p=p.parentElement){
   const o=getComputedStyle(p);if(o.overflow!=='visible'||o.overflowX!=='visible')return p;}return null;};
 const vw=document.documentElement.clientWidth;
 const push=(t,o)=>bad.push(Object.assign({t},o));

 // 1. A painted box escaping the frame. Deliberate scroll regions and SVG
 //    internals are exempt; everything else must fit.
 for(const n of document.querySelectorAll('.viz-wrapper *')){
   if(n.ownerSVGElement||!shown(n)||scrollableAncestor(n))continue;
   const b=n.getBoundingClientRect(); if(!b.width&&!b.height)continue;
   if(b.right>vw+1||b.left<-1)
     push('escapes frame',{el:n.tagName+'.'+String(n.className).slice(0,24),
       right:Math.round(b.right),vw,txt:(n.textContent||'').trim().slice(0,26)});
 }

 // 2. Control text cut off, excluding a deliberate ellipsis.
 for(const n of document.querySelectorAll(
     '.viz-wrapper button,.viz-wrapper label,.viz-wrapper .control-label,'+
     '.viz-wrapper output,.viz-wrapper select')){
   if(!shown(n)||scrollableAncestor(n))continue;
   if(getComputedStyle(n).textOverflow==='ellipsis')continue;
   const selfClip=getComputedStyle(n).overflow!=='visible'&&
     (n.scrollWidth>n.clientWidth+1||n.scrollHeight>n.clientHeight+1);
   const anc=clipAncestor(n);
   let ancClip=false;
   if(anc){const a=n.getBoundingClientRect(),p=anc.getBoundingClientRect();
     ancClip=a.right>p.right+1||a.left<p.left-1||a.bottom>p.bottom+1||a.top<p.top-1;}
   if(selfClip||ancClip)
     push('clipped control text',{el:n.tagName,txt:n.textContent.trim().slice(0,30)});
   // A nowrap label wider than its own padding box spills OUTSIDE the control
   // even when overflow is visible, so nothing is technically clipped. It still
   // reads as broken: on a selected pill the dark background stops short and
   // the white text carries on over the panel. Figure 10's "Change" did this at
   // 320px, 8px past its box, and the clip checks above could not see it.
   if(getComputedStyle(n).whiteSpace==='nowrap'&&n.scrollWidth>n.clientWidth+1)
     push('label wider than its control',{el:n.tagName,
       txt:n.textContent.trim().slice(0,24),
       needs:n.scrollWidth,has:n.clientWidth});
 }

 // 3. SVG text cut off by a clipping ancestor. The text is inside the <svg> box
 //    but the <svg> itself overflows its panel, so nothing else looks wrong —
 //    this is how figure 3 silently lost 45px of its x-axis title at 320px.
 for(const t of document.querySelectorAll('svg text')){
   const txt=(t.textContent||'').trim(); if(!txt)continue;
   const b=t.getBoundingClientRect(); if(!b.width)continue;
   const anc=clipAncestor(t); if(!anc)continue;
   const p=anc.getBoundingClientRect();
   const lost=Math.max(0,b.right-p.right)+Math.max(0,p.left-b.left);
   if(lost>2){push('svg text clipped',{txt:txt.slice(0,36),lostPx:Math.round(lost),
     by:anc.tagName+'.'+String(anc.className).slice(0,18)});continue;}
   // Not formally overflowing, but close enough to be cut anyway: a glyph's ink
   // can extend past the advance width the layout box reports. Figure 12's
   // x-axis title finished 1px inside its panel at 320px, so the test above
   // passed while the rendered label actually read "...recipient GI".
   //
   // 2px of clearance is the bar. It is deliberately small: a centred edge tick
   // legitimately sits close to the panel — figure 7's "$100,000" clears by 8px
   // and is entirely readable — so this flags only text with essentially no room
   // left, which is where the cut-off letter appears.
   // A scroll container is exempt: content past its edge is reachable, not lost.
   // Figure 2's y-axis title sits 2px beyond its chart-wrap, which scrolls.
   const ancOv=getComputedStyle(anc);
   if(/auto|scroll/.test(ancOv.overflowX)||/auto|scroll/.test(ancOv.overflow))continue;
   const clearance=Math.min(p.right-b.right,b.left-p.left);
   if(clearance<2)push('svg text has no clearance, letters get cut',
     {txt:txt.slice(0,36),clearancePx:Math.round(clearance),
      by:anc.tagName+'.'+String(anc.className).slice(0,18)});
 }

 // 4. Overlapping axis/annotation text inside a plot.
 for(const svg of document.querySelectorAll('svg')){
   const texts=[...svg.querySelectorAll('text')]
     .filter(t=>shown(t)&&(t.textContent||'').trim());
   const label=t=>/tick|axis|label|annot|note/i.test(t.getAttribute('class')||'')||!!t.closest('.axis');
   const ax=texts.filter(label);
   for(let i=0;i<ax.length;i++)for(let j=i+1;j<ax.length;j++){
     const a=ax[i].getBoundingClientRect(),b=ax[j].getBoundingClientRect();
     if(!a.width||!b.width)continue;
     if(a.left<b.right-1&&a.right>b.left+1&&a.top<b.bottom-1&&a.bottom>b.top+1)
       push('axis label overlap',{a:ax[i].textContent.trim().slice(0,18),
         b:ax[j].textContent.trim().slice(0,18)});}}

 // 5. Overlapping control groups.
 for(const p of document.querySelectorAll('.controls')){
   if(!shown(p))continue;
   const kids=[...p.children].filter(shown);
   for(let i=0;i<kids.length;i++)for(let j=i+1;j<kids.length;j++){
     const a=kids[i].getBoundingClientRect(),b=kids[j].getBoundingClientRect();
     if(a.left<b.right-1&&a.right>b.left+1&&a.top<b.bottom-1&&a.bottom>b.top+1)
       push('controls overlap',{a:kids[i].textContent.trim().slice(0,20),
         b:kids[j].textContent.trim().slice(0,20)});}}

 // 6. Tap targets. WCAG 2.2 counts an activating label as part of the target,
 //    so a 15px checkbox on a 24px line is a 24px target — measure the union.
 for(const n of document.querySelectorAll(
     '.viz-wrapper button,.viz-wrapper select,.viz-wrapper input[type=checkbox]')){
   if(!shown(n))continue;
   let h=n.getBoundingClientRect().height;
   if(n.type==='checkbox'){
     const lab=(n.id&&document.querySelector('label[for="'+CSS.escape(n.id)+'"]'))||n.closest('label');
     if(lab&&shown(lab)){const b=n.getBoundingClientRect(),l=lab.getBoundingClientRect();
       h=Math.max(b.bottom,l.bottom)-Math.min(b.top,l.top);}}
   if(h>0&&h<cfg.minTap)
     push('tap target too small',{txt:(n.textContent||n.id||n.type).trim().slice(0,22),
       h:Math.round(h),min:cfg.minTap});}

 // 7. Editable inputs below 16px zoom-jump on iOS. Non-negotiable.
 for(const n of document.querySelectorAll(
     'input:not([type=checkbox]):not([type=radio]):not([type=hidden]),textarea')){
   if(!shown(n))continue;
   const fs=parseFloat(getComputedStyle(n).fontSize);
   if(fs<cfg.minInput-0.1)push('editable input below 16px',{id:n.id||n.type,fs});}

 // 8. Text below the note floor.
 for(const n of document.querySelectorAll('.viz-wrapper *')){
   if(n.children.length||n.ownerSVGElement)continue;
   const txt=(n.textContent||'').trim(); if(!txt||!shown(n))continue;
   const fs=parseFloat(getComputedStyle(n).fontSize);
   if(fs<cfg.minText-0.05)push('text below floor',{txt:txt.slice(0,24),fs,min:cfg.minText});}
 for(const t of document.querySelectorAll('svg text')){
   const txt=(t.textContent||'').trim(); if(!txt||!shown(t))continue;
   const fs=parseFloat(getComputedStyle(t).fontSize);
   if(fs<cfg.minText-0.05)push('svg text below floor',{txt:txt.slice(0,24),fs,min:cfg.minText});}

 // 9. A <select> whose value matches no option renders BLANK, and nothing else
 //    about the page looks wrong.
 for(const sel of document.querySelectorAll('select')){
   if(!shown(sel))continue;
   if(sel.selectedIndex===-1)push('select shows no selected option',{id:sel.id||'?',value:sel.value});}

 // 10. A native <select> clips its option text silently: no scrollWidth, no
 //     overflow, just an unreadable label. This is how figure 3's income filter
 //     came to read "All income g" at every width — 113px of text in 97px of
 //     room — while every other check passed.
 //
 //     The bar is that the selected option fits, full stop. It was 0.6 on the
 //     assumption that some truncation is unavoidable at 320px; it is not, once
 //     a select stops reserving 30px for a chevron it does not draw and takes a
 //     full grid row where half a row is too narrow. The 0.98 tolerance absorbs
 //     the difference between canvas measurement and rendered text.
 const cv=document.createElement('canvas').getContext('2d');
 for(const sel of document.querySelectorAll('select')){
   if(!shown(sel))continue;
   const cs=getComputedStyle(sel);
   cv.font=cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;
   const txt=sel.selectedOptions[0]?sel.selectedOptions[0].text:'';
   const inner=sel.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
   const w=cv.measureText(txt).width;
   if(txt&&w>0&&inner/w<0.98)
     push('select option text does not fit',{id:sel.id||'?',txt:txt.slice(0,34),
       visibleFraction:+(inner/w).toFixed(2),needs:Math.round(w),has:Math.round(inner)});}

 // 10b. Controls in one bank must share a height or the row reads as ragged.
 //      Nine of the twelve figures had two or three different heights sitting
 //      side by side, because the shared layer left each control's height to its
 //      own font-size and padding.
 //
 //      A segmented toggle that has wrapped to two rows is exempt: below 400px a
 //      three-option toggle reflows rather than shrinking its labels, and being
 //      taller is the whole point of that.
 for(const bank of document.querySelectorAll('.controls,.remit-viz__controls')){
   if(!shown(bank))continue;
   const items=[...bank.querySelectorAll(
     'select,.segmented,.remit-viz__toggle,.toggle,.country-trigger,'
     +'.combo__button,.select-trigger,.search-select')].filter(shown);
   const seen=new Map();
   for(const el of items){
     const btns=[...el.querySelectorAll('button')].filter(shown);
     const rows=new Set(btns.map(x=>Math.round(x.getBoundingClientRect().top))).size;
     if(rows>1)continue;                       // a wrapped pill bank, legitimately taller
     const h=Math.round(el.getBoundingClientRect().height);
     if(!seen.has(h))seen.set(h,String(el.className).split(' ')[0]||el.tagName);
   }
   if(seen.size>1)
     push('controls in one bank have different heights',
       {found:[...seen.entries()].map(function(e){return e[0]+'px:'+e[1];})});}

 // 11. Trailing blank space on a control row. A wrapped row that stops short
 //     leaves a bare stripe of panel, which reads as a missing control.
 for(const p of document.querySelectorAll('.controls')){
   if(!shown(p))continue;
   const cs=getComputedStyle(p),box=p.getBoundingClientRect();
   const right=box.right-parseFloat(cs.paddingRight),left=box.left+parseFloat(cs.paddingLeft);
   // Controls on one row do not share a top: a two-line label pushes its control
   // down. Group by vertical overlap, not by a rounded top.
   const lines=[];
   for(const k of [...p.children].filter(shown)){
     const b=k.getBoundingClientRect(); if(!b.height)continue;
     const line=lines.find(l=>b.top<l.bottom-4&&b.bottom>l.top+4);
     if(line){line.top=Math.min(line.top,b.top);line.bottom=Math.max(line.bottom,b.bottom);
       line.r=Math.max(line.r,b.right);}
     else lines.push({top:b.top,bottom:b.bottom,r:b.right});}
   for(const v of lines){const slack=right-v.r;
     if(slack>cfg.maxSlack&&right-left>200)
       push('blank space on control row',{slack:Math.round(slack),max:cfg.maxSlack});}}

 // 12. Focus must be visible. A control with no outline, ring or border change
 //     on :focus-visible is unusable by keyboard.
 // 13. Most checks above scope to `.viz-wrapper *`. A figure without that root
 //     would pass every one of them by having nothing to examine, which is how
 //     figures 2 and 10 once went green. Fail loudly instead.
 if(!document.querySelector('.viz-wrapper'))
   push('no .viz-wrapper root, so scoped checks did not run',{});

 // 14. Keyboard focus must be visible. These figures suppress the browser ring
 //     with outline:none and substitute a background tint, which is legitimate —
 //     so this compares the computed style focused against unfocused and accepts
 //     ANY visible difference, rather than insisting on an outline. It caught
 //     figure 10's legend toggles, whose rule was
 //     `:focus-visible:not(.active)` while all three start active, so focusing
 //     one changed nothing at all.
 //
 //     Runs last: it moves focus, and a text input would open its menu, so
 //     inputs and disabled controls are left alone.
 const focusProps=['outlineStyle','outlineWidth','outlineColor','boxShadow',
   'backgroundColor','borderColor','color','textDecorationLine',
   'stroke','strokeWidth','strokeOpacity','fill','fillOpacity','opacity','r'];
 const focusSnap=el=>{const cs=getComputedStyle(el);
   return focusProps.map(p=>cs[p]).join('|');};
 const wasFocused=document.activeElement;
 for(const el of document.querySelectorAll(
     '.viz-wrapper button, .viz-wrapper select, .viz-wrapper [tabindex="0"]')){
   if(el.disabled||!shown(el))continue;
   if(/^(INPUT|TEXTAREA)$/.test(el.tagName))continue;
   const before=focusSnap(el);
   el.focus({preventScroll:true});
   const after=focusSnap(el);
   el.blur();
   if(before===after)
     push('no visible focus indicator',{el:el.tagName,
       txt:(el.textContent||'').trim().slice(0,20),
       cls:String(el.className).slice(0,24)});
 }
 if(wasFocused&&wasFocused.focus)wasFocused.focus({preventScroll:true});

 const marks=document.querySelectorAll(cfg.markSelector);
 return {bad,marks:marks.length,
   overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
   bodyH:Math.round(document.body.getBoundingClientRect().height)};
}"""


def static_checks(repo):
    """Checks that do not need a browser: pinned deps, SRI, embed contract."""
    problems = []
    for path in sorted(glob.glob(os.path.join(repo, '[0-9]*.html'))):
        name = os.path.basename(path)
        src = open(path, encoding='utf-8').read()

        for tag in re.findall(r'<script[^>]*\ssrc="(https?://[^"]+)"[^>]*>', src):
            problems.append(f'{name}: external script not vendored: {tag}')

        # Any runtime fetch at all, not just a third-party one. fetch() from a
        # file:// origin is blocked by CORS, so a same-origin .json fetch breaks
        # opening the figure from disk — which is how vendoring the map geometry
        # as .json broke figure 4 until it became a classic script.
        for url in re.findall(r"""(?:d3\.json|d3\.text|d3\.csv|fetch)\(\s*['"]([^'"]+)['"]""", src):
            problems.append(f'{name}: runtime fetch breaks file:// viewing: {url}')

        # Every referenced local script must exist, or the figure loads with no
        # data and the failure is a blank chart rather than an error.
        for ref in re.findall(r'<script[^>]*\ssrc="(?!https?://)([^"?]+)(?:\?[^"]*)?"', src):
            if not os.path.isfile(os.path.join(repo, ref)):
                problems.append(f'{name}: references a missing file: {ref}')

        # A figure with a data file must actually load it.
        slug = name[:-5]
        data_file = os.path.join(repo, 'data', slug + '.js')
        if os.path.isfile(data_file) and f'data/{slug}.js' not in src:
            problems.append(f'{name}: data/{slug}.js exists but is not loaded')
        if 'shared/cgd-embed.js' not in src:
            problems.append(f'{name}: does not load shared/cgd-embed.js')
        if 'cgdRendered' not in src:
            problems.append(f'{name}: never announces cgd:rendered, so CGD_READY never fires')
        if not re.search(r'data-cgd-interactive-name="[a-z0-9-]+"', src):
            problems.append(f'{name}: missing or non-kebab data-cgd-interactive-name')

    embed = open(os.path.join(repo, 'shared', 'cgd-embed.js'), encoding='utf-8').read()
    if "'*'" in embed or '"*"' in embed:
        problems.append('shared/cgd-embed.js: wildcard postMessage origin')
    if 'https://www.cgdev.org' not in embed:
        problems.append('shared/cgd-embed.js: production parent origin missing')
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('figures', nargs='*', help='figure numbers to check (default: all)')
    ap.add_argument('--shots', metavar='DIR', help='also write full-page screenshots')
    ap.add_argument('--widths', help='comma-separated widths (default: %s)'
                    % ','.join(map(str, WIDTHS)))
    args = ap.parse_args()

    os.chdir(REPO)
    widths = [int(w) for w in args.widths.split(',')] if args.widths else list(WIDTHS)
    figs = sorted(glob.glob('[0-9]*.html'), key=lambda f: int(f.split('-')[0]))
    if args.figures:
        figs = [f for f in figs if f.split('-')[0] in args.figures]
    if args.shots:
        os.makedirs(args.shots, exist_ok=True)

    cfg = {'minTap': MIN_TAP_PX, 'minInput': MIN_INPUT_PX, 'minText': MIN_TEXT_PX,
           'maxSlack': 48, 'markSelector': MARK_SELECTOR}

    failures = 0
    print('== static checks ==')
    static = static_checks(REPO)
    for p in static:
        print('  FAIL', p)
    failures += len(static)
    if not static:
        print('  clean')

    handler = functools.partial(Quiet, directory='.')
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(('127.0.0.1', PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    print('\n== render checks ==')
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for f in figs:
            lines = []
            for w in widths:
                page = browser.new_page(viewport={'width': w, 'height': 900})
                errors = []
                page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{PORT}/{f}', wait_until='load', timeout=90000)
                try:
                    page.wait_for_function('window.CGD_READY===true', timeout=45000)
                except Exception:
                    lines.append(f'  {w}px  FAIL never reached CGD_READY')
                    failures += 1
                    page.close()
                    continue
                r = page.evaluate(AUDIT, cfg)
                if args.shots:
                    page.screenshot(path=f'{args.shots}/{f.split("-")[0]}-{w}.png',
                                    full_page=True)

                problems = []
                seen = set()
                for item in r['bad']:
                    key = json.dumps(item, sort_keys=True)[:90]
                    if key in seen:
                        continue
                    seen.add(key)
                    problems.append(json.dumps(item, sort_keys=True))
                if r['overflow'] > 1:
                    problems.append(json.dumps({'t': 'page scrolls horizontally',
                                                'px': r['overflow']}))
                if r['marks'] == 0:
                    problems.append(json.dumps({'t': 'no marks rendered'}))
                for e in errors[:2]:
                    problems.append(json.dumps({'t': 'console error', 'msg': e[:140]}))

                if problems:
                    lines.append(f'  {w}px  bodyH={r["bodyH"]} marks={r["marks"]}')
                    lines.extend('      ' + p for p in problems)
                    failures += len(problems)
                page.close()
            print(f + ('   clean' if not lines else ''))
            print('\n'.join(lines))
            sys.stdout.flush()
        browser.close()
    srv.shutdown()

    print(f'\nTOTAL FAILURES: {failures}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
