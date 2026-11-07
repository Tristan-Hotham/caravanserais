// QA and figure renders: node code/qa_shot.js <shots.json>
// shots.json: {"base":"http://127.0.0.1:8793/caravanserais/index.html","shots":[{"out":"qa/x.png","w":1280,"h":800,"dpr":1,"q":"maponly=1&b=..","full":false,"wait":4000,"eval":"..."}]}
// MapLibre from a local npm copy (MAPLIBRE_DIST); DEM tiles from a local cache (DEM) if given; OpenFreeMap live.
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
(async () => {
  const cfg = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const ML = process.env.MAPLIBRE_DIST || '/tmp/ml/node_modules/maplibre-gl/dist';
  const px = process.env.HTTPS_PROXY ? ['--proxy-server=' + process.env.HTTPS_PROXY, '--proxy-bypass-list=127.0.0.1;localhost'] : [];
  const browser = await chromium.launch({ args: [...px, '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const errors = [];
  for (const s of cfg.shots) {
    const ctx = await browser.newContext({ viewport: { width: s.w || 1280, height: s.h || 800 }, deviceScaleFactor: s.dpr || 1, ignoreHTTPSErrors: true, colorScheme: s.scheme || 'light' });
    const page = await ctx.newPage();
    await page.route(/cdn\.jsdelivr\.net\/npm\/maplibre-gl@4\.7\.1\/dist\/(.*)/, (route, req) => { const f = path.join(ML, req.url().split('/dist/')[1]); route.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith('.css') ? 'text/css' : 'application/javascript' }); });
    await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
    page.on('console', m => { if (m.type() === 'error') errors.push(`[${s.out}] ${m.text().slice(0, 300)}`); });
    page.on('pageerror', e => errors.push(`[${s.out}] pageerror: ${e.message}`));
    const q = (s.q || '') + (cfg.dem ? `&dem=${encodeURIComponent(cfg.dem)}&demmax=4` : '');
    await page.goto(cfg.base + '?' + q, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__cvReady, null, { timeout: 90000 }).catch(e => errors.push(`[${s.out}] not ready`));
    await page.evaluate(() => new Promise(res => { const m = window.__map; if (!m) return res(); m.once('idle', () => setTimeout(res, 800)); setTimeout(res, 40000); }));
    if (s.check) console.log('check', s.out, JSON.stringify(await page.evaluate(s.check)));
    if (s.eval) { await page.evaluate(s.eval); await page.waitForTimeout(s.wait || 2500); }
    await page.screenshot({ path: s.out, fullPage: !!s.full, type: s.out.endsWith('.jpg') ? 'jpeg' : 'png', quality: s.out.endsWith('.jpg') ? 88 : undefined, timeout: 180000 });
    console.log('ok', s.out);
    await ctx.close();
  }
  await browser.close();
  console.log('ERRORS:\n' + errors.join('\n'));
})();
