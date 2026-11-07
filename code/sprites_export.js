// Export the pen drawings (js/caravan-art.js) as PNGs for the collage and header: node code/sprites_export.js <base url of code/sheet.html> <outdir>
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto(process.argv[2]); await p.waitForFunction(() => window.CaravanArt);
  const out = await p.evaluate(() => { window.__cvK = 5;
    const r = {};
    for (const d of Object.keys(CaravanArt.DYN)) { r['inn-' + d] = CaravanArt.sheet('inn', d).toDataURL(); r['urban-' + d] = CaravanArt.sheet('urban', d).toDataURL(); }
    r['ruin-none'] = CaravanArt.sheet('ruin', 'none').toDataURL(); r['ribat'] = CaravanArt.sheet('ribat').toDataURL(); r['camels'] = CaravanArt.sheet('camels').toDataURL();
    return r;
  });
  fs.mkdirSync(process.argv[3], { recursive: true });
  for (const [k, v] of Object.entries(out)) fs.writeFileSync(`${process.argv[3]}/${k}.png`, Buffer.from(v.split(',')[1], 'base64'));
  console.log(Object.keys(out).length, 'sprites'); await b.close();
})();
