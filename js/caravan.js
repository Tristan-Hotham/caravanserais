/* Caravanserais of the Silk Roads: the study's layers on The Inked World (../ink-map/js/ink-map.js).
 * Every caravanserai as a pen drawing washed in its dynasty's colour, the inferred links between neighbours, camel trains
 * walking those links, filters by era and kind, a search and popups. Dr Tristan Hotham, Independent researcher, 2026. MIT. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  if (qs.has('maponly')) document.body.classList.add('maponly');
  if (qs.has('clean')) document.body.classList.add('clean');
  const ENGINE = '../ink-map/';
  const V = '?v=cv1';
  const DYN = [  // key, label, years: the same order as code/02_analyse.py
    ['early', 'Before the Seljuks', 'before about 1040'], ['seljuk', 'Seljuk', 'about 1040 to 1308'], ['ilkhanid', 'Ilkhanid and Timurid', 'about 1256 to 1507'],
    ['mamluk', 'Mamluk', '1250 to 1517'], ['ottoman', 'Ottoman', 'about 1300 to 1922'], ['safavid', 'Safavid', '1501 to 1736'],
    ['mughal', 'Mughal and Suri', '1526 to 1857'], ['qajar', 'Afsharid, Zand and Qajar', '1736 to 1925'], ['modern', 'Modern', 'after 1925'],
    ['other', 'Other or regional', ''], ['none', 'Undated', '']];
  const DLAB = Object.fromEntries(DYN.map(d => [d[0], d[1]]));
  const SETL = { roadside: 'Roadside caravanserai', urban: 'Town or city khan', ribat: 'Ribat: a fort or Sufi lodge, not an inn' };
  const PRESETS = [
    ['Silk Roads', [[18, 21], [82, 45]]],
    ['Anatolia', [[25.5, 35.6], [44.8, 42.2]]],
    ['Iran', [[44, 25], [63.5, 39.8]]],
    ['Levant', [[33.5, 30.8], [45.5, 37.6]]],
    ['Central Asia', [[52, 29], [75, 43]]],
    ['Grand Trunk Road', [[68, 25.5], [81, 34.5]]],
  ];
  let map, DATA = null, ROUTES = null;
  const state = { dyn: new Set(DYN.map(d => d[0])), set: new Set(['roadside', 'urban', 'ribat']) };

  // ---------------- map
  const pre = document.getElementById('presets');
  PRESETS.forEach(([n, b]) => {
    const btn = document.createElement('button'); btn.className = 'chip'; btn.textContent = n;
    btn.addEventListener('click', () => map && map.fitBounds(b, { padding: 20, duration: 2200, essential: true }));
    pre.appendChild(btn);
  });
  const opts = { base: new URL(ENGINE, location.href).href };
  if (qs.get('tj')) opts.tilejson = qs.get('tj');
  if (qs.get('dem')) opts.dem = qs.get('dem');
  if (qs.get('demmax')) opts.demMax = +qs.get('demmax');
  const start = qs.get('at') ? qs.get('at').split(',').map(Number) : null;
  const bounds = qs.get('b') ? qs.get('b').split(',').map(Number) : null;
  const mob = matchMedia('(max-width:600px)').matches;
  const mo = start ? { center: [start[1], start[0]], zoom: start[2] } : (mob && !bounds) ? { center: [45, 35.5], zoom: 3.55 } : { bounds: bounds ? [[bounds[0], bounds[1]], [bounds[2], bounds[3]]] : (mob ? [[26, 24], [64, 44]] : PRESETS[0][1]), fitBoundsOptions: { padding: 10 } };
  // the Inked World remembers its winter look in this browser (shared with the Inked World page): this map is drawn in
  // summer, so the stored choice is put back as it was after the switch
  let wint = null; try { wint = localStorage.getItem('ink-winter'); } catch (e) {}
  InkMap.create('map', Object.assign(opts, { mapOptions: mo })).then(m => {
    map = window.__map = m;
    if (InkMap.setWinter) InkMap.setWinter(map, false);
    try { if (wint === null) localStorage.removeItem('ink-winter'); else localStorage.setItem('ink-winter', wint); } catch (e) {}
    document.getElementById('nojs').remove();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const fold = () => { const at = document.querySelector('.maplibregl-ctrl-attrib.maplibregl-compact'); if (at) { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); } };
    map.once('idle', fold); map.on('resize', () => setTimeout(fold, 50)); fold();
    map.getSource && map.getStyle();
    if (window.InkExtras) { InkExtras.scaleBar(map, document.getElementById('scalebar')); document.getElementById('rose').innerHTML = InkExtras.compassSVG(58); }
    const isDark = () => { const r = document.documentElement; return r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; };
    const tone = () => InkMap.setSeaTone && InkMap.setSeaTone(map, isDark());
    tone(); new MutationObserver(tone).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    CaravanArt.register(map);
    // the engine's own Wikidata heritage drawings would draw many caravanserais twice: off until asked for
    InkMap.setGroup(map, 'heritage', false);
    ['animals', 'flight'].forEach(g => InkMap.setGroup(map, g, false));
    return Promise.all([fetch('data/caravanserais.geojson' + V).then(r => r.json()), fetch('data/routes_inferred.geojson' + V).then(r => r.json())]);
  }).then(([d, r]) => {
    DATA = d; ROUTES = r;
    addLayers(); setupLayers(); setupSearch(); setupPopups(); camels();
    window.__cvReady = true;
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });

  function firstNameLayer() {
    const l = map.getStyle().layers.find(x => x.type === 'symbol' && x.metadata && x.metadata.group === 'names');
    return l ? l.id : undefined;
  }
  function addLayers() {
    for (const f of DATA.features) {
      const p = f.properties;
      p.icon = p.setting === 'ribat' ? 'cv-ribat' : (p.setting === 'urban' ? 'cv-urban-' : (p.ruin ? 'cv-ruin-' : 'cv-inn-')) + (p.setting === 'ribat' ? '' : p.dynasty);
      p.label = p.name || p.native || '';
    }
    map.addSource('cv', { type: 'geojson', data: DATA, attribution: 'Caravanserais: <a href="https://www.wikidata.org/" target="_blank">Wikidata</a> (CC0), <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> (ODbL)' });
    map.addSource('cvroutes', { type: 'geojson', data: ROUTES });
    const before = firstNameLayer();
    map.addLayer({ id: 'cv-routes', type: 'line', source: 'cvroutes', minzoom: 2.5, layout: { 'line-cap': 'round' },
      paint: { 'line-color': '#8C3A1E', 'line-opacity': ['interpolate', ['linear'], ['zoom'], 2.5, 0.7, 6, 0.85], 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 1.3, 7, 2.2, 11, 3], 'line-dasharray': [2, 1.6] } });
    map.addLayer({ id: 'cv-icons', type: 'symbol', source: 'cv',
      layout: { 'icon-image': ['get', 'icon'], 'icon-size': ['interpolate', ['linear'], ['zoom'], 2, 0.5, 4, 0.66, 6, 0.85, 9, 1.05, 13, 1.35], 'icon-allow-overlap': true, 'icon-ignore-placement': false,
        'icon-anchor': 'bottom', 'symbol-sort-key': ['-', 0, ['get', 'sl']], 'symbol-z-order': 'viewport-y' } });
    map.addLayer({ id: 'cv-names', type: 'symbol', source: 'cv', minzoom: 7,
      layout: { 'text-field': ['get', 'label'], 'text-font': ['Ink Italic'], 'text-size': ['interpolate', ['linear'], ['zoom'], 7, 12, 12, 15], 'text-anchor': 'top', 'text-offset': [0, 0.3],
        'text-optional': true, 'text-max-width': 9, 'symbol-sort-key': ['-', 0, ['get', 'sl']], 'text-padding': 3 },
      paint: { 'text-color': '#A3261B', 'text-halo-color': 'rgba(243,229,191,0.92)', 'text-halo-width': 1.6 } });
    applyFilter();
  }
  function filterExpr() {
    return ['all', ['in', ['get', 'dynasty'], ['literal', [...state.dyn]]], ['in', ['get', 'setting'], ['literal', [...state.set]]]];
  }
  function applyFilter() {
    if (!map.getLayer('cv-icons')) return;
    const f = filterExpr();
    map.setFilter('cv-icons', f); map.setFilter('cv-names', f);
    const n = DATA.features.filter(x => state.dyn.has(x.properties.dynasty) && state.set.has(x.properties.setting)).length;
    const el = document.getElementById('cvCount'); if (el) el.textContent = n.toLocaleString('en-GB') + ' shown';
  }

  // ---------------- layers panel: the engine's groups, the plain modern map, and this study's layers and filters
  function setupLayers() {
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    // era checkboxes, with a little wash swatch in each dynasty's colour
    const dl = document.getElementById('dynList');
    const counts = {}; DATA.features.forEach(f => counts[f.properties.dynasty] = (counts[f.properties.dynasty] || 0) + 1);
    for (const [k, lab, yrs] of DYN) {
      if (!counts[k]) continue;
      const l = document.createElement('label');
      l.innerHTML = `<input type="checkbox" data-dyn="${k}" checked> <span class="sw" style="background:${CaravanArt.DYN[k]}"></span> ${lab} <span class="n">${counts[k]}</span>`;
      if (yrs) l.title = yrs;
      dl.appendChild(l);
    }
    lp.querySelectorAll('input[data-dyn]').forEach(b => b.addEventListener('change', () => { b.checked ? state.dyn.add(b.dataset.dyn) : state.dyn.delete(b.dataset.dyn); applyFilter(); }));
    lp.querySelectorAll('input[data-set]').forEach(b => b.addEventListener('change', () => { b.checked ? state.set.add(b.dataset.set) : state.set.delete(b.dataset.set); applyFilter(); }));
    document.getElementById('allDyn').addEventListener('click', e => { e.preventDefault(); const on = state.dyn.size < DYN.length; lp.querySelectorAll('input[data-dyn]').forEach(b => { b.checked = on; on ? state.dyn.add(b.dataset.dyn) : state.dyn.delete(b.dataset.dyn); }); if (on) DYN.forEach(d => state.dyn.add(d[0])); applyFilter(); });
    const vis = (id, on) => map.getLayer(id) && map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
    document.getElementById('routeBox').addEventListener('change', e => vis('cv-routes', e.target.checked));
    document.getElementById('camelBox').addEventListener('change', e => { camelsOn = e.target.checked; camelShow(); });
    document.getElementById('cvBox').addEventListener('change', e => { vis('cv-icons', e.target.checked); vis('cv-names', e.target.checked); });
    // the engine's own groups
    const boxes = [...lp.querySelectorAll('input[data-g]')];
    const modern = document.getElementById('modern');
    const NAME_LAYERS = map.getStyle().layers.filter(l => l.type === 'symbol' && l.metadata && ['names', 'rivers'].includes(l.metadata.group)).map(l => l.id);
    const saved = {};
    NAME_LAYERS.forEach(id => saved[id] = { c: map.getPaintProperty(id, 'text-color'), h: map.getPaintProperty(id, 'text-halo-color') });
    function apply() {
      const m = modern.checked;
      boxes.forEach(b => { const g = b.dataset.g; const inkOnly = ['mountains', 'forests', 'biomes', 'sea', 'farms', 'tint'].includes(g); InkMap.setGroup(map, g, b.checked && !(m && inkOnly)); });
      InkMap.setGroup(map, 'paper', !m); InkMap.setGroup(map, 'modern', m); InkMap.setGroup(map, 'coast', !m);
      if (m) InkMap.setGroup(map, 'roads', false);
      NAME_LAYERS.forEach(id => {
        map.setPaintProperty(id, 'text-color', m ? (map.getLayer(id).metadata.group === 'rivers' ? '#2D6A9F' : '#333333') : saved[id].c);
        map.setPaintProperty(id, 'text-halo-color', m ? 'rgba(255,255,255,0.9)' : saved[id].h);
      });
      if (map.getLayer('rivers')) map.setPaintProperty('rivers', 'line-color', m ? '#7FB2D9' : InkMap.INK.blue);
    }
    boxes.forEach(b => b.addEventListener('change', apply)); modern.addEventListener('change', apply);
    const rose = document.getElementById('rose'), cb = document.getElementById('compassBox');
    cb.addEventListener('change', () => { rose.style.display = cb.checked ? '' : 'none'; });
    applyFilter();
  }

  // ---------------- search: the caravanserais by name, then places from the Inked World gazetteer
  function norm(s) { return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug');
    let G = null, sel = -1, items = [];
    const own = DATA.features.filter(f => f.properties.label).map(f => ({ n: f.properties.label, k: norm(f.properties.label + ' ' + f.properties.native), lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1], z: 12.5, ctx: f.properties.country + ' · caravanserai', id: f.properties.id }));
    const load = () => G || (G = fetch(ENGINE + 'data/gazetteer.json').then(r => r.json()).then(a => a.map(r => ({ n: r[0], k: norm(r[0]), lon: r[1], lat: r[2], z: r[3], ctx: r[5] || r[4] }))).catch(() => []));
    q.addEventListener('focus', load);
    async function run() {
      const t = norm(q.value.trim());
      if (t.length < 2) { sug.style.display = 'none'; return; }
      const a = own.filter(r => r.k.includes(t)).sort((x, y) => (x.k.startsWith(t) ? 0 : 1) - (y.k.startsWith(t) ? 0 : 1)).slice(0, 7);
      const g = (await load()).filter(r => r.k.startsWith(t)).slice(0, 10 - a.length);
      items = a.concat(g); sel = -1;
      sug.innerHTML = items.map((r, i) => `<li role="option" data-i="${i}">${esc(r.n)} <span>${esc(r.ctx || '')}</span></li>`).join('');
      sug.style.display = items.length ? 'block' : 'none';
    }
    function go(r) {
      if (!r) return; sug.style.display = 'none'; q.value = r.n; q.blur();
      map.flyTo({ center: [r.lon, r.lat], zoom: r.z, duration: 2400, essential: true });
      if (r.id) map.once('moveend', () => { const f = DATA.features.find(x => x.properties.id === r.id); if (f) popup(f); });
    }
    q.addEventListener('input', run);
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(0, Math.min(items.length - 1, sel + (e.key === 'ArrowDown' ? 1 : -1))); [...sug.children].forEach((li, i) => li.setAttribute('aria-selected', i === sel)); }
      if (e.key === 'Enter') { e.preventDefault(); go(items[sel >= 0 ? sel : 0]); }
      if (e.key === 'Escape') sug.style.display = 'none';
    });
    sug.addEventListener('click', e => { const li = e.target.closest('li'); if (li) go(items[+li.dataset.i]); });
  }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

  // ---------------- popups
  let pop = null;
  function popup(f) {
    const p = f.properties;
    const name = p.name || p.native || 'An unnamed caravanserai';
    const L = [];
    L.push(`<b class="t">${esc(name)}</b>`);
    if (p.native && p.native !== p.name) L.push(`<div class="nat">${esc(p.native)}</div>`);
    L.push(`<div>${esc(p.country)} · ${esc(SETL[p.setting])}</div>`);
    let d = DLAB[p.dynasty] || 'Undated';
    if (p.year) d += ` · built ${p.year_how === 'century' ? 'in the century around ' + p.year : (p.year_how === 'decade' ? 'in the ' + p.year + 's' : 'in ' + p.year)}`;
    else if (p.dynasty !== 'none') d += ' (from its style in Wikidata)';
    L.push(`<div><span class="sw" style="background:${CaravanArt.DYN[p.dynasty]}"></span> ${esc(d)}</div>`);
    if (p.styles && p.styles.length) L.push(`<div class="mut">Style: ${esc(p.styles.join(', '))}</div>`);
    if (p.heritage && p.heritage.length) L.push(`<div class="mut">Listed: ${esc([...new Set(p.heritage)].join(', '))}</div>`);
    if (p.ruin) L.push('<div class="mut">Mapped as a ruin</div>');
    if (p.reuse) L.push('<div class="mut">Now reused (hotel, guest house, museum or restaurant)</div>');
    if (p.setting !== 'ribat' && p.gap != null) {
      const g = Math.round(p.gap);
      L.push(`<div class="gap">Nearest other stop: <b>${g} km</b>${p.nbr ? ' (' + esc(p.nbr) + ')' : ''}${p.here > 1 ? `; ${p.here} inns share this stop` : ''}</div>`);
    }
    const links = [];
    if (p.qid) links.push(`<a href="https://www.wikidata.org/wiki/${p.qid}" target="_blank" rel="noopener">Wikidata</a>`);
    if (p.enwiki) links.push(`<a href="${esc(p.enwiki)}" target="_blank" rel="noopener">Wikipedia</a>`);
    if (p.osm && p.osm.length) links.push(`<a href="https://www.openstreetmap.org/${p.osm[0]}" target="_blank" rel="noopener">OpenStreetMap</a>`);
    if (links.length) L.push(`<div class="lk">${links.join(' · ')}</div>`);
    if (pop) pop.remove();
    pop = new maplibregl.Popup({ maxWidth: '300px', offset: [0, -14] }).setLngLat(f.geometry.coordinates).setHTML(L.join('')).addTo(map);
  }
  function setupPopups() {
    map.on('click', 'cv-icons', e => { if (e.features && e.features.length) { const id = e.features[0].properties.id; popup(DATA.features.find(f => f.properties.id === id) || e.features[0]); } });
    map.on('mouseenter', 'cv-icons', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'cv-icons', () => map.getCanvas().style.cursor = '');
  }

  // ---------------- camel trains: walk the inferred links between neighbouring caravanserais, a day's stage in about six seconds
  let camelsOn = !qs.has('nocamels'), camelShow = () => {};
  function camels() {
    const nodes = new Map(), adj = new Map();
    const key = c => c[0].toFixed(4) + ',' + c[1].toFixed(4);
    for (const f of ROUTES.features) {
      const [a, b] = f.geometry.coordinates, ka = key(a), kb = key(b);
      nodes.set(ka, a); nodes.set(kb, b);
      (adj.get(ka) || adj.set(ka, []).get(ka)).push([kb, f.properties.km]);
      (adj.get(kb) || adj.set(kb, []).get(kb)).push([ka, f.properties.km]);
    }
    const keys = [...adj.keys()].filter(k => adj.get(k).length >= 1);
    // one train for about every eight links, seeded so every visit starts the same way
    let s = 20260; const R = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
    const N = Math.min(90, Math.round(ROUTES.features.length / 8));
    const T = [];
    for (let i = 0; i < N; i++) {
      const a = keys[Math.floor(R() * keys.length)], nb = adj.get(a), [b, km] = nb[Math.floor(R() * nb.length)];
      T.push({ a, b, km, t: R(), prev: null });
    }
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const STAGE_S = 6, STAGE_KM = 34;   // a stage of 34 km (a day's march) passes in 6 seconds
    let last = performance.now(), acc = 0;
    function pos(tr) { const A = nodes.get(tr.a), B = nodes.get(tr.b); return [A[0] + (B[0] - A[0]) * tr.t, A[1] + (B[1] - A[1]) * tr.t]; }
    // the trains are small HTML markers (a symbol layer fed many times a second never finishes fading in)
    const url = CaravanArt.sheet('camels').toDataURL();
    for (const tr of T) {
      const el = document.createElement('img'); el.src = url; el.alt = ''; el.className = 'camel'; el.setAttribute('aria-hidden', 'true');
      tr.el = el; tr.mk = new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat(pos(tr)).addTo(map);
    }
    function size() {
      const z = map.getZoom(), w = Math.round(z < 6 ? 22 + (z - 4.2) * 5 : Math.min(48, 31 + (z - 6) * 3.5));
      for (const tr of T) tr.el.style.width = w + 'px';
    }
    camelShow = () => { const on = camelsOn && map.getZoom() >= 4.2; for (const tr of T) tr.el.style.display = on ? '' : 'none'; };
    map.on('zoom', () => { size(); camelShow(); }); size(); camelShow();
    function draw() {
      for (const tr of T) {
        const A = nodes.get(tr.a), B = nodes.get(tr.b);
        tr.mk.setLngLat(pos(tr)); tr.el.style.transform = tr.el.style.transform.replace(/ ?scaleX\(-1\)/, '');
        tr.el.classList.toggle('flip', B[0] < A[0]);
      }
    }
    function step(now) {
      const dt = Math.min(0.5, (now - last) / 1000); last = now; acc += dt;
      if (camelsOn && !document.hidden && map.getZoom() >= 4.2 && acc > 0.05) {
        for (const tr of T) {
          tr.t += acc * (STAGE_KM / STAGE_S) / Math.max(tr.km, 1);
          if (tr.t >= 1) {
            const nb = adj.get(tr.b).filter(x => x[0] !== tr.a);
            const pick = nb.length ? nb[Math.floor(R() * nb.length)] : [tr.a, tr.km];
            tr.t = 0; tr.a = tr.b; tr.b = pick[0]; tr.km = pick[1];
          }
        }
        acc = 0; draw();
      }
      if (!reduce) requestAnimationFrame(step);
    }
    draw();
    if (!reduce) requestAnimationFrame(step);
    window.__camels = T;
  }

  // ---------------- the key: the drawings themselves
  (function key() {
    const el = document.getElementById('key'); if (!el) return;
    const add = (c, label) => { const d = document.createElement('div'); d.appendChild(c); const s = document.createElement('span'); s.innerHTML = label; d.appendChild(s); el.appendChild(d); };
    const h = t => { const x = document.createElement('h3'); x.textContent = t; el.appendChild(x); };
    h('Buildings');
    add(CaravanArt.sheet('inn', 'none'), 'Roadside caravanserai');
    add(CaravanArt.sheet('urban', 'none'), 'Khan in a town or city');
    add(CaravanArt.sheet('ruin', 'none'), 'Caravanserai mapped as a ruin');
    add(CaravanArt.sheet('ribat', 'none'), 'Ribat: a fort or Sufi lodge <i>(not an inn)</i>');
    add(CaravanArt.sheet('camels', 'none'), 'Camel train on an inferred link <i>(illustration)</i>');
    const r = document.createElement('canvas'); r.width = 92; r.height = 30; const x = r.getContext('2d'); x.strokeStyle = '#8C5A2E'; x.lineWidth = 2.4; x.setLineDash([5, 5]); x.beginPath(); x.moveTo(4, 15); x.lineTo(88, 15); x.stroke();
    add(r, 'Inferred link between neighbouring stops <i>(not a mapped road)</i>');
    h('Courtyard wash: who built it');
    for (const [k, lab, yrs] of DYN) add(CaravanArt.sheet('inn', k), lab + (yrs ? ` <i>(${yrs})</i>` : ''));
  })();

  // ---------------- cartouche folding, as on The Inked World
  const ct = document.getElementById('cartouche'), ctT = document.getElementById('ctToggle');
  const foldC = f => { ct.classList.toggle('folded', f); ctT.setAttribute('aria-expanded', String(!f)); };
  if (mob) foldC(true);
  ctT.addEventListener('click', () => foldC(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => foldC(true));
  document.addEventListener('fullscreenchange', () => { if (document.fullscreenElement) foldC(true); });
  const th = document.getElementById('theme');
  th.addEventListener('click', () => { const r = document.documentElement; const dark = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = dark ? 'light' : 'dark'; });
})();
