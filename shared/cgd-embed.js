(function () {
  'use strict';

  const PRODUCTION_PARENT_ORIGIN = 'https://www.cgdev.org';
  const PREVIEW_PARENT_ORIGINS = new Set([
    'https://center-for-global-development.github.io'
  ]);
  const interactiveName = document.documentElement.dataset.cgdInteractiveName;
  let lastHeight = 0;
  let viewSent = false;
  let activeDetailLabel = '';
  let compactMode = null;

  function visibleViewportWidth() {
    const widths = [
      window.visualViewport && window.visualViewport.width,
      document.documentElement && document.documentElement.clientWidth,
      window.innerWidth
    ].map(Number).filter(value => Number.isFinite(value) && value > 0);
    return widths.length ? Math.min.apply(null, widths) : 930;
  }

  function syncResponsiveMode() {
    const nextCompact = visibleViewportWidth() <= 600;
    document.documentElement.classList.toggle('cgd-mobile-embed', nextCompact);
    document.documentElement.dataset.cgdViewport = nextCompact ? 'compact' : 'wide';

    const fullscreen = document.querySelector('.fullscreen-btn');
    const touchDevice = (navigator.maxTouchPoints || 0) > 0 ||
      (window.matchMedia && window.matchMedia('(pointer: coarse)').matches);
    if (fullscreen) fullscreen.hidden = nextCompact || touchDevice;

    if (compactMode !== nextCompact) {
      compactMode = nextCompact;
      window.dispatchEvent(new CustomEvent('cgd:viewportchange', {
        detail: { width: visibleViewportWidth(), compact: nextCompact }
      }));
    }
  }

  window.CGDViewport = Object.freeze({
    width: visibleViewportWidth,
    compact: function () { return visibleViewportWidth() <= 600; }
  });

  syncResponsiveMode();
  window.addEventListener('resize', syncResponsiveMode);
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', syncResponsiveMode);
  }
  queueMicrotask(function () {
    window.dispatchEvent(new Event('resize'));
  });

  function targetParentOrigin() {
    try {
      const referrer = new URL(document.referrer);
      if (PREVIEW_PARENT_ORIGINS.has(referrer.origin)) return referrer.origin;
      if (
        referrer.protocol === 'http:' &&
        (referrer.hostname === '127.0.0.1' || referrer.hostname === 'localhost')
      ) {
        return referrer.origin;
      }
    } catch (error) {
      // No usable referrer: retain the production-only target.
    }
    return PRODUCTION_PARENT_ORIGIN;
  }

  function postToParent(message) {
    if (window.parent === window) return;
    window.parent.postMessage(message, targetParentOrigin());
  }

  function reportHeight() {
    const height = Math.ceil(document.body.getBoundingClientRect().height);
    if (!height || height === lastHeight) return;
    lastHeight = height;
    postToParent({ type: 'cgd-iframe-resize', height });
  }

  function sendAnalytics(event, details) {
    if (!interactiveName) return;
    postToParent(Object.assign({
      type: 'cgd_analytics',
      event,
      interactive_name: interactiveName
    }, details || {}));
  }

  function actionValue(target) {
    const dataKeys = ['year', 'view', 'metric', 'role', 'mode', 'rank', 'sort', 'scope', 'direction', 'value', 'id'];
    for (const key of dataKeys) {
      if (target.dataset && target.dataset[key]) return target.dataset[key];
    }
    if ('value' in target && target.value) return String(target.value);
    const label = target.getAttribute && (target.getAttribute('aria-label') || target.textContent);
    return label ? label.trim().replace(/\s+/g, ' ').slice(0, 120) : undefined;
  }

  function trackAction(actionType, actionLabel, target) {
    if (actionType === 'detail_open') activeDetailLabel = actionLabel;
    if (actionType === 'detail_close' && actionLabel === 'active_detail') {
      actionLabel = activeDetailLabel || 'detail';
    }
    const value = actionValue(target);
    const details = {
      action_type: actionType,
      action_label: actionLabel
    };
    if (value) details.action_value = value;
    sendAnalytics('interactive_engagement', details);
  }

  const pageRules = {
    '1-data-coverage-gaps.html': [
      ['#yearToggle button', 'filter', 'year'],
      ['#viewToggle button', 'view_control', 'coverage_view'],
      ['#limitSelect', 'filter', 'corridor_limit'],
      ['#countrySelect .select-option', 'filter', 'country'],
      ['#regionLegend button, #regionLegend [role="button"]', 'filter', 'region'],
      ['#recipientChart .bar-col', 'detail_open', 'country_detail'],
      ['.corridor-action', 'detail_open', 'corridor_detail'],
      ['#popupClose', 'detail_close', 'country_detail'],
      ['#corridorPopupClose', 'detail_close', 'corridor_detail']
    ],
    '2-model-v-wb.html': [
      ['#incomeSelect .combo__option', 'filter', 'income_group'],
      ['#countrySelect .combo__option', 'filter', 'country'],
      ['#year2021, #year2024', 'filter', 'year']
    ],
    '3-total-remittance-flows.html': [
      ['#incomeSelect', 'filter', 'income_group'],
      ['#countrySelect .select-option', 'filter', 'country'],
      ['#regionLegend button, #regionLegend [role="button"]', 'filter', 'region']
    ],
    '4-remittances-map.html': [
      ['#directionToggle button', 'view_control', 'flow_direction'],
      ['#yearToggle button', 'filter', 'year'],
      ['#scopeToggle button', 'view_control', 'map_scope'],
      ['#pickerOptions [role="option"]', 'filter', 'country'],
      ['#mapSvg .country', 'detail_open', 'country_detail'],
      ['#mapSvg .flow', 'detail_open', 'corridor_detail'],
      ['#popupClose', 'detail_close', 'active_detail']
    ],
    '5-remittance-flows-regions.html': [
      ['#yearToggle button', 'filter', 'year'],
      ['#metricToggle button', 'view_control', 'metric'],
      ['#heatGrid button, #heatGrid [role="button"]', 'detail_open', 'matrix_cell'],
      ['[data-popup-page]', 'navigate', 'corridor_page'],
      ['#popupClose', 'detail_close', 'matrix_cell']
    ],
    '6-remittance-flows-incomes.html': [
      ['#yearToggle button', 'filter', 'year'],
      ['#metricToggle button', 'view_control', 'metric'],
      ['#heatGrid button, #heatGrid [role="button"]', 'detail_open', 'matrix_cell'],
      ['[data-popup-page]', 'navigate', 'corridor_page'],
      ['#popupClose', 'detail_close', 'matrix_cell']
    ],
    '7-migrant-stock-vs-gni.html': [
      ['#metricToggle button', 'view_control', 'metric'],
      ['#regionSelect', 'filter', 'region'],
      ['#countrySelect .select-option', 'filter', 'country'],
      ['#incomeLegend button, #incomeLegend [role="button"]', 'filter', 'income_group'],
      ['#scatterSvg .point', 'detail_open', 'country_detail'],
      ['[data-popup-page]', 'navigate', 'destination_page'],
      ['#popupClose', 'detail_close', 'country_detail']
    ],
    '8-remittances-source-dependence.html': [
      ['#metricToggle button', 'view_control', 'metric'],
      ['#incomeSelect', 'filter', 'income_group'],
      ['#countrySelect .select-option', 'filter', 'country'],
      ['#regionLegend button, #regionLegend [role="button"]', 'filter', 'region'],
      ['#scatterSvg .point', 'detail_open', 'country_detail'],
      ['#corridorSort button', 'view_control', 'corridor_sort'],
      ['#popupClose', 'detail_close', 'country_detail']
    ],
    '9-remittance-source-importance.html': [
      ['#metricToggle button', 'view_control', 'metric'],
      ['#incomeSelect', 'filter', 'income_group'],
      ['#countrySelect .select-option', 'filter', 'country'],
      ['#regionLegend button, #regionLegend [role="button"]', 'filter', 'region'],
      ['#scatterSvg .point', 'detail_open', 'country_detail'],
      ['#corridorSort button', 'view_control', 'corridor_sort'],
      ['.info-btn[data-info="average"]', 'detail_open', 'metric_definition'],
      ['#metricInfoClose', 'detail_close', 'metric_definition'],
      ['#popupClose', 'detail_close', 'country_detail']
    ],
    '10-remittances-vs-oda-fdi.html': [
      ['#incomeFilter', 'filter', 'income_group'],
      ['#countryOptions .country-option', 'filter', 'country'],
      ['#roleToggle button', 'view_control', 'country_role'],
      ['#modeToggle button', 'view_control', 'comparison_mode'],
      ['#rankToggle button', 'view_control', 'ranking_metric'],
      ['#prevPage', 'navigate', 'previous_page'],
      ['#nextPage', 'navigate', 'next_page']
    ],
    '11-total-remittances-vs-gni.html': [
      ['#incomeSelect', 'filter', 'income_group'],
      ['#countrySelect .select-option', 'filter', 'country'],
      ['#regionLegend button, #regionLegend [role="button"]', 'filter', 'region']
    ],
    '12-remittance-corridors-vs-gni.html': [
      ['#roleToggle button', 'view_control', 'country_role'],
      ['#countrySelect .select-option', 'filter', 'country'],
      ['#limitSelect', 'filter', 'corridor_limit'],
      ['#regionFilter button, #regionFilter [role="button"]', 'filter', 'region'],
      ['#prevPage', 'navigate', 'previous_page'],
      ['#nextPage', 'navigate', 'next_page'],
      ['#popupClose', 'detail_close', 'corridor_detail']
    ]
  };

  const pageName = decodeURIComponent(location.pathname.split('/').pop() || '');
  const rules = pageRules[pageName] || [];
  rules.push(['#fullscreenBtn', 'view_control', 'fullscreen']);

  function matchingRule(target) {
    for (const rule of rules) {
      const matched = target.closest(rule[0]);
      if (matched) return { matched, actionType: rule[1], actionLabel: rule[2] };
    }
    return null;
  }

  document.addEventListener('click', function (event) {
    const rule = matchingRule(event.target);
    if (rule && !/^(SELECT|INPUT)$/.test(rule.matched.tagName)) {
      trackAction(rule.actionType, rule.actionLabel, rule.matched);
    }
  });

  document.addEventListener('change', function (event) {
    const rule = matchingRule(event.target);
    if (rule && /^(SELECT|INPUT)$/.test(rule.matched.tagName)) {
      trackAction(rule.actionType, rule.actionLabel, rule.matched);
    }
  });

  window.CGDTracking = Object.freeze({
    engagement: function (actionType, actionLabel, actionValue) {
      const details = {
        action_type: actionType,
        action_label: actionLabel
      };
      if (actionValue !== undefined && actionValue !== null && actionValue !== '') {
        details.action_value = String(actionValue);
      }
      sendAnalytics('interactive_engagement', details);
    },
    reportHeight
  });

  function reportView() {
    if (viewSent) return;
    viewSent = true;
    sendAnalytics('interactive_view');
    reportHeight();
  }

  window.addEventListener('load', reportView, { once: true });

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(reportHeight);
  }

  if ('ResizeObserver' in window) {
    new ResizeObserver(reportHeight).observe(document.body);
  } else {
    window.addEventListener('resize', reportHeight);
  }

  if (document.readyState === 'complete') {
    queueMicrotask(reportView);
  }
}());
