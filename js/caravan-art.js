/* Caravanserais of the Silk Roads: pen drawings for the map, in the hand of The Inked World (js/ink-palette.js).
 * A roadside caravanserai (walled courtyard, corner towers, a tall portal), a city khan (two storeys of arcades and a dome),
 * a ribat (a fort with a watchtower), a ruined caravanserai, and a little camel train. The courtyard of each building is
 * washed in the colour of its dynasty, as on a hand-coloured plan. Every drawing is original.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function (global) {
  'use strict';
  const PAL = global.InkPalette || {};
  const INK = PAL.ink || '#2B2119', PAPER = PAL.paperFill || 'rgba(243,229,191,0.97)', PAPERL = PAL.paperLight || '#FBF3DC', RED = PAL.red || '#A3261B';
  const PG = PAL.pigments || {};
  const K = ((PAL.SCALE) || 3) / 2;
  // dynasty washes (muted pigments; undated buildings stay paper)
  const DYN = {
    early: '#8A6A4E', seljuk: '#B4472E', ilkhanid: '#5C7896', mamluk: '#C9A24A', ottoman: '#6E8A50', safavid: '#3E9BA6',
    mughal: '#D08A4A', qajar: '#C27597', modern: '#9A958A', other: '#B9AC88', none: '#F3E5BF',
  };
  function rng(seed) { let s = seed >>> 0 || 1; return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return ((s >>> 0) % 100000) / 100000; }; }
  function rgba(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; }

  function Pen(w, h, seed, k) {
    k = k || global.__cvK || K;   // __cvK: a larger scale for exported drawings (code/sprites_export.js)
    const c = document.createElement('canvas'); c.width = Math.ceil(w * k); c.height = Math.ceil(h * k); c.__k = k;
    const x = c.getContext('2d', { willReadFrequently: true }); x.scale(k, k); x.lineCap = 'round'; x.lineJoin = 'round'; x.strokeStyle = INK;
    const R = rng(seed || 11), j = a => (R() - 0.5) * a;
    const p = {
      c, x,
      path(pts, close) { x.beginPath(); pts.forEach((q, i) => { const a = q[0] + j(0.5), b = q[1] + j(0.5); i ? x.lineTo(a, b) : x.moveTo(a, b); }); if (close) x.closePath(); return p; },
      line(pts, lw, col) { x.lineWidth = lw || 1.3; x.strokeStyle = col || INK; p.path(pts); x.stroke(); x.strokeStyle = INK; return p; },
      poly(pts, fill, lw) { p.path(pts, true); if (fill) { x.fillStyle = fill; x.fill(); } if (lw !== 0) { x.lineWidth = lw || 1.8; x.stroke(); } return p; },
      rect(a, b, w0, h0, fill, lw) { return p.poly([[a, b], [a + w0, b], [a + w0, b + h0], [a, b + h0]], fill, lw); },
      arch(cx, base, w0, h0, fill, lw) {   // a pointed arch, base at y = base
        const l = cx - w0 / 2, r = cx + w0 / 2, sp = base - h0 + w0 * 0.55;
        x.beginPath(); x.moveTo(l + j(0.3), base); x.lineTo(l, sp);
        x.quadraticCurveTo(l + w0 * 0.05, base - h0 + w0 * 0.12, cx, base - h0);
        x.quadraticCurveTo(r - w0 * 0.05, base - h0 + w0 * 0.12, r, sp); x.lineTo(r + j(0.3), base);
        if (fill) { x.closePath(); x.fillStyle = fill; x.fill(); }
        x.lineWidth = lw || 1.1; x.stroke(); return p;
      },
      hatch(a, b, w0, h0, step, lw) {   // diagonal shading inside a box
        x.save(); x.beginPath(); x.rect(a, b, w0, h0); x.clip(); x.lineWidth = lw || 0.7; x.strokeStyle = 'rgba(43,33,25,0.6)';
        for (let t = -h0; t < w0; t += step || 2.4) { x.beginPath(); x.moveTo(a + t + j(0.4), b + h0); x.lineTo(a + t + h0 + j(0.4), b); x.stroke(); }
        x.restore(); x.strokeStyle = INK; return p;
      },
      tower(cx, base, tw, th, fill) {   // a round corner tower: a short cylinder with a domed cap
        const l = cx - tw / 2, t = base - th;
        x.beginPath(); x.moveTo(l, base); x.lineTo(l, t + tw * 0.3);
        x.quadraticCurveTo(cx, t - tw * 0.45, l + tw, t + tw * 0.3); x.lineTo(l + tw, base);
        x.fillStyle = fill || PAPER; x.fill(); x.lineWidth = 1.5; x.stroke();
        p.line([[l + tw * 0.62, t + tw * 0.5], [l + tw * 0.62, base - 0.6]], 0.6, 'rgba(43,33,25,0.55)');
        p.line([[l + tw * 0.8, t + tw * 0.55], [l + tw * 0.8, base - 0.6]], 0.6, 'rgba(43,33,25,0.55)');
        return p;
      },
      ground(a, b, y) { p.line([[a, y], [b, y]], 1.1); for (let i = 0; i < 4; i++) { const t = a + (b - a) * (0.08 + 0.26 * i); p.line([[t, y + 2], [t + 4, y + 2]], 0.6); } return p; },
    };
    return p;
  }

  // the roadside caravanserai: a walled courtyard seen from above and in front, four iwans round the court, round corner
  // towers and a tall portal (pishtaq) in the middle of the front wall
  function inn(dyn, ruin) {
    const W = 52, H = 44, p = Pen(W, H, 31 + dyn.length * 7 + (ruin ? 3 : 0)), x = p.x;
    const wash = DYN[dyn] || DYN.none, gy = 39;
    const top = 12, fy = 25;                 // back of the court, front of the wall top
    // courtyard (the wall top as a parallelogram, the open court inside it)
    p.poly([[7, fy], [45, fy], [48, top], [10, top]], PAPER, 1.6);
    p.poly([[12, fy - 2.2], [40.5, fy - 2.2], [42.5, top + 2.4], [14, top + 2.4]], dyn === 'none' ? PAPERL : rgba(wash, 0.75), 0.9);
    // iwans: the deep arched halls in the middle of each side of the court
    p.arch(28.4, top + 6.2, 4.4, 4.2, 'rgba(43,33,25,0.55)', 0.8);
    p.line([[13.6, fy - 6], [14.6, top + 7]], 1.6, 'rgba(43,33,25,0.55)');
    p.line([[41.6, fy - 6], [42.4, top + 7]], 1.6, 'rgba(43,33,25,0.55)');
    // a well or cistern in the court
    x.beginPath(); x.ellipse(27.5, fy - 7.4, 1.6, 0.9, 0, 0, Math.PI * 2); x.fillStyle = 'rgba(61,110,158,0.75)'; x.fill(); x.lineWidth = 0.6; x.stroke();
    // the front wall
    if (ruin) {
      p.poly([[7, fy], [16, fy], [17.5, fy + 2], [20, fy + 1], [20, gy], [7, gy]], PAPER, 1.6);
      p.poly([[33, fy + 3], [36, fy + 1], [39, fy + 4], [45, fy + 2], [45, gy], [33, gy]], PAPER, 1.6);
      p.poly([[20, fy + 5], [24, fy + 3.4], [28, fy + 6], [33, fy + 4.6], [33, gy], [20, gy]], PAPER, 1.6);
      p.hatch(38, fy + 4, 7, gy - fy - 4, 2.6);
      p.tower(7, gy, 7, 13);
      p.arch(26.5, gy, 5.6, 8.5, 'rgba(43,33,25,0.85)', 1);
      for (const [a, b] of [[48, gy - 1], [3, gy - 0.6], [30, gy + 0.2], [46, gy - 0.4]]) p.poly([[a, b], [a + 2, b - 1.4], [a + 3.4, b]], PAPER, 0.8);
    } else {
      p.rect(7, fy, 38, gy - fy, PAPER, 1.8);
      p.hatch(38.5, fy + 1, 6.3, gy - fy - 1, 2.4);
      // blind arches along the front
      for (const cx of [11.5, 15.5, 37, 41]) p.arch(cx, gy - 3, 2.4, 4.5, null, 0.7);
      // the corner towers
      p.tower(7, gy, 7.2, 17); p.tower(45, gy, 7.2, 17, 'rgba(231,210,160,0.97)');
      // the portal: a tall frame standing proud of the wall, with its arch, door and a band of inscription
      p.rect(19.5, fy - 7, 14, gy - fy + 7, PAPER, 1.8);
      p.line([[19.5, fy - 4.6], [33.5, fy - 4.6]], 0.7);
      x.fillStyle = rgba(wash === DYN.none ? '#C9A24A' : wash, 0.8); x.fillRect(21.2, fy - 3.8, 10.6, 1.8);
      p.arch(26.5, gy - 0.5, 9, 12.5, dyn === 'none' ? 'rgba(201,162,74,0.35)' : rgba(wash, 0.55), 1);
      p.arch(26.5, gy, 4.6, 7.6, 'rgba(43,33,25,0.88)', 1);
      p.line([[19.5, fy - 7], [33.5, fy - 7]], 1.4);
    }
    p.ground(1, 51, gy + 1.5);
    return p.c;
  }

  // a city khan: a two-storey block of arcaded rooms round a court, with a small dome over the gate
  function khan(dyn) {
    const W = 50, H = 44, p = Pen(W, H, 77 + dyn.length * 5), x = p.x;
    const wash = DYN[dyn] || DYN.none, gy = 39, top = 11, fy = 19;
    p.poly([[6, fy], [44, fy], [47, top], [9, top]], PAPER, 1.5);
    p.poly([[10, fy - 2], [40.5, fy - 2], [42.5, top + 2], [12, top + 2]], dyn === 'none' ? PAPERL : rgba(wash, 0.75), 0.8);
    p.rect(6, fy, 38, gy - fy, PAPER, 1.8);
    p.hatch(38, fy + 1, 6, gy - fy - 1, 2.4);
    p.line([[6, fy + 9.5], [44, fy + 9.5]], 1);
    for (let i = 0; i < 7; i++) { const cx = 9.4 + i * 5.2; p.arch(cx, fy + 8.6, 3, 5.6, i === 3 ? null : 'rgba(43,33,25,0.5)', 0.7); }
    for (let i = 0; i < 7; i++) { const cx = 9.4 + i * 5.2; if (i === 3) continue; p.arch(cx, gy - 1, 3.2, 6.4, 'rgba(43,33,25,0.62)', 0.8); }
    // the gate and its dome
    p.arch(25, gy, 6, 10, 'rgba(43,33,25,0.88)', 1.1);
    x.beginPath(); x.moveTo(20.5, fy); x.quadraticCurveTo(25, fy - 11, 29.5, fy); x.closePath(); x.fillStyle = dyn === 'none' ? PAPER : rgba(wash, 0.85); x.fill(); x.lineWidth = 1.4; x.stroke();
    p.line([[25, fy - 6.4], [25, fy - 9.6]], 1);
    p.ground(1, 49, gy + 1.5);
    return p.c;
  }

  // a ribat: a square fort with round towers and a tall round watchtower (as at Monastir and Sousse)
  function ribat(dyn) {
    const W = 46, H = 50, p = Pen(W, H, 151), x = p.x, gy = 45, fy = 30, top = 22;
    p.poly([[6, fy], [38, fy], [41, top], [9, top]], PAPER, 1.5);
    p.rect(6, fy, 32, gy - fy, PAPER, 1.8);
    p.hatch(33, fy + 1, 5, gy - fy - 1, 2.4);
    for (let i = 0; i < 7; i++) p.rect(7 + i * 4.4, fy - 2.2, 2.2, 2.2, PAPER, 0.9);
    p.tower(6, gy, 7, 18); p.tower(38, gy, 7, 18, 'rgba(231,210,160,0.97)');
    p.tower(30, fy + 1, 7, 26, PAPER);
    p.line([[26.6, fy - 20], [33.4, fy - 20]], 0.8);
    p.arch(20, gy, 4.6, 7.4, 'rgba(43,33,25,0.88)', 1);
    // a red pennant, the mark of a frontier fort
    p.line([[30, fy - 25], [30, fy - 31]], 0.9); x.beginPath(); x.moveTo(30, fy - 31); x.lineTo(36, fy - 29.5); x.lineTo(30, fy - 28); x.fillStyle = RED; x.fill();
    p.ground(1, 45, gy + 1.5);
    return p.c;
  }

  // a camel train: a driver on foot and three laden camels, nose to tail on a halter rope
  function camels(dir) {
    const W = 72, H = 30, p = Pen(W, H, 211), x = p.x, gy = 26;
    if (dir === 'l') { x.translate(W, 0); x.scale(-1, 1); }
    function camel(ox, load, s) {
      s = s || 1;
      const P = (a, b) => [ox + a * s, gy - b * s];
      // legs
      for (const [a, b] of [[3, 0], [5.4, 0], [12.6, 0], [15, 0]]) p.line([P(a, 8), P(a + (a < 8 ? -0.6 : 0.6), b)], 1.1);
      // body and hump, neck and head (facing right)
      x.beginPath(); const q = [P(1.5, 9.5), P(3, 14), P(8, 18.5), P(12, 14.6), P(15.5, 15.2), P(17.4, 12.6), P(16.6, 8.6), P(10, 7.8), P(3, 8.2)];
      x.moveTo(...q[0]); for (let i = 1; i < q.length; i++) x.lineTo(...q[i]); x.closePath();
      x.fillStyle = 'rgba(214,190,128,0.95)'; x.fill(); x.lineWidth = 1.3; x.stroke();
      p.line([P(17, 12.8), P(19.6, 16.6), P(21, 20.2), P(23.6, 20), P(24, 18.6), P(21.8, 17.6)], 1.3);
      p.line([P(1.6, 9.5), P(0.2, 6)], 0.8);   // tail
      if (load) {   // bundles slung either side of the hump
        x.fillStyle = load; p.poly([P(5.6, 15.4), P(10.6, 15.6), P(11, 11.2), P(5.4, 11.2)], load, 1);
        p.line([P(8, 18.2), P(8.2, 11.2)], 0.7);
      }
    }
    // the driver, on foot at the front with a staff
    const dx = 62;
    p.line([[dx, gy - 1], [dx + 1, gy - 7]], 1.1); p.line([[dx + 2.4, gy - 1], [dx + 1.2, gy - 7]], 1.1);
    p.poly([[dx - 1.2, gy - 6.6], [dx + 3.6, gy - 6.6], [dx + 2.8, gy - 13.4], [dx + 0.2, gy - 13.4]], 'rgba(180,71,46,0.85)', 1);
    x.beginPath(); x.arc(dx + 1.5, gy - 15.2, 1.8, 0, Math.PI * 2); x.fillStyle = PAPER; x.fill(); x.lineWidth = 1; x.stroke();
    p.line([[dx + 4.6, gy - 1], [dx + 6.2, gy - 17]], 0.9);
    camel(39, 'rgba(180,71,46,0.8)', 0.95); camel(20, 'rgba(102,128,156,0.8)', 0.9); camel(2, 'rgba(201,162,74,0.85)', 0.85);
    p.line([[39 + 23.5 * 0.95, gy - 19], [dx + 1, gy - 10]], 0.5);   // halter ropes
    p.line([[20 + 23.5 * 0.9, gy - 18], [39 + 1.5, gy - 9]], 0.5);
    p.line([[2 + 23.5 * 0.85, gy - 17], [20 + 1.5, gy - 8.5]], 0.5);
    p.line([[0, gy + 0.8], [W, gy + 0.8]], 0.5, 'rgba(43,33,25,0.35)');
    return p.c;
  }

  function toImage(c) { return c.getContext('2d').getImageData(0, 0, c.width, c.height); }
  const KINDS = ['inn', 'urban', 'ribat', 'ruin'];
  function register(map) {
    const add = (id, c) => { if (!map.hasImage(id)) map.addImage(id, toImage(c), { pixelRatio: 2 * c.__k }); };
    for (const d of Object.keys(DYN)) { add('cv-inn-' + d, inn(d)); add('cv-urban-' + d, khan(d)); add('cv-ruin-' + d, inn(d, true)); }
    add('cv-ribat', ribat('none'));
    add('cv-camels-r', camels('r')); add('cv-camels-l', camels('l'));
  }
  function sheet(kind, dyn) {
    if (kind === 'ribat') return ribat('none');
    if (kind === 'camels') return camels('r');
    return kind === 'urban' ? khan(dyn) : inn(dyn, kind === 'ruin');
  }
  global.CaravanArt = { register, sheet, DYN, KINDS };
})(window);
