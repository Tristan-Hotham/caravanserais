"""header.png: the 1200 x 630 social card (parchment, title left, a crop of the ink map right)."""
from PIL import Image, ImageDraw, ImageFont
from common import *

R = jload(f"{DATA}/results.json"); T = R["text"]
W, H = 1200, 630
img = Image.new("RGB", (W, H), (246, 238, 216)); d = ImageDraw.Draw(img)
m = Image.open(os.path.join(ROOT, "img", "map_silk.jpg")).convert("RGB")
# crop Anatolia to Iran from the 1600 x 900 render, scale to the right-hand panel
c = m.crop((40, 57, 1280, 900)).resize((640, 435), Image.LANCZOS)
X, Y = 520, 98
img.paste(c, (X, Y)); d.rectangle([X - 1, Y - 1, X + 640, Y + 435], outline=(43, 33, 25), width=4)
d.rectangle([X + 8, Y + 8, X + 632, Y + 427], outline=(43, 33, 25), width=1)
f = lambda n, s: ImageFont.truetype(os.path.join(FONTS, n), s)
fr = ImageFont.truetype(os.path.join(FONTS, "FrauncesVar.ttf"), 64)
try: fr.set_variation_by_axes([144, 900])
except Exception: pass
d.rectangle([40, 62, 190, 92], fill=(163, 38, 27)); d.text((52, 66), "DATA STUDY", font=f("IBMPlexMono-Medium.ttf", 19), fill="white")
d.text((40, 112), "Caravan-\nserais of\nthe Silk\nRoads", font=fr, fill=(43, 33, 25), spacing=2)
d.text((42, 412), f"{R['n']:,} caravanserais, khans and\nribats from open data, drawn in ink.", font=f("SourceSerif4-Regular.ttf", 22), fill=(43, 33, 25), spacing=5)
d.text((42, 478), f"One dynasty at a time, the Safavid\ncaravanserais of Iran stand {T['saf_median']:.0f} km\napart: a day's march.", font=f("SourceSerif4-It.ttf", 22), fill=(163, 38, 27), spacing=5)
d.text((42, 584), "Dr Tristan Hotham · Independent researcher · 2026", font=f("IBMPlexMono-Regular.ttf", 15), fill=(110, 96, 78))
d.text((W - 40, 584), "maps.tristanhotham.com/caravanserais", font=f("IBMPlexMono-Medium.ttf", 15), fill=(43, 33, 25), anchor="ra")
img.save(os.path.join(ROOT, "header.png"), optimize=True)
print("header.png", img.size)
