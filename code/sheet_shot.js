// node code/sheet_shot.js <url> <out.png> [w] [h]: screenshot a sheet page (QA of the pen drawings)
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +(process.argv[4] || 1400), height: +(process.argv[5] || 900) } });
  p.on('console', m => console.log('console', m.type(), m.text())); p.on('pageerror', e => console.log('pageerror', e.message));
  await p.goto(process.argv[2]); await p.waitForTimeout(500); await p.screenshot({ path: process.argv[3], fullPage: true }); await b.close();
})();
