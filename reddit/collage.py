"""The Reddit collage: the Silk Roads on The Inked World with every caravanserai, region callouts on the seas, a spacing
histogram and a full legend, on a light parchment sheet. Input: a render of the page (code/qa_shot.js, maponly&clean&nocamels,
2800 x 1700, bounds 19,22.5 to 79,46) saved as WORK/../scr/collage_base.png, and the pen drawings in img/sprites/."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from common import *

R = jload(f"{DATA}/results.json"); T = R["text"]
BASE = "/home/claude/work/new6/caravanserais/scr/collage_base.png"
SP = os.path.join(ROOT, "img", "sprites")
OUT = os.path.join(ROOT, "reddit", "caravanserais_of_the_silk_roads.png")
F = {"disp": f"{FONTS}/FrauncesVar.ttf", "ser": f"{FONTS}/SourceSerif4-Regular.ttf", "seri": f"{FONTS}/SourceSerif4-It.ttf",
     "sb": f"{FONTS}/SourceSerif4-Semibold.ttf", "mono": f"{FONTS}/IBMPlexMono-Regular.ttf", "monom": f"{FONTS}/IBMPlexMono-Medium.ttf"}
font = lambda k, s: ImageFont.truetype(F[k], s)


def fr(s, w=900):
    f = ImageFont.truetype(F["disp"], s)
    try: f.set_variation_by_axes([144, w])
    except Exception: pass
    return f


INKC_ = (43, 33, 25); RED_ = (163, 38, 27); MUT = (110, 96, 78); PAP = (246, 238, 216)
W = 2800; MAPH = 1700; TOP = 330; BOT = 820; H = TOP + MAPH + BOT
img = Image.new("RGB", (W, H), PAP)
d = ImageDraw.Draw(img)

# ---- map, with a double ink frame
base = Image.open(BASE).convert("RGB")
assert base.size == (2800, 1700), base.size
img.paste(base, (0, TOP))
d.rectangle([0, TOP, W - 1, TOP + MAPH], outline=INKC_, width=6)
d.rectangle([14, TOP + 14, W - 15, TOP + MAPH - 14], outline=INKC_, width=2)

# the page's fitBounds([19,22.5],[79,46], padding 10) in Web Mercator, to place callouts by longitude and latitude
def merc(lat): return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
x0, x1, y0, y1 = math.radians(19), math.radians(79), merc(22.5), merc(46)
k = min((W - 20) / (x1 - x0), (MAPH - 20) / (y1 - y0))
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
def px(lon, lat): return (W / 2 + (math.radians(lon) - cx) * k, TOP + MAPH / 2 - (merc(lat) - cy) * k)


def halo_text(xy, text, f, fill, anchor="la", halo=PAP, r=7):
    lay = Image.new("L", img.size, 0); ld = ImageDraw.Draw(lay)
    ld.multiline_text(xy, text, font=f, fill=255, anchor=anchor, spacing=6)
    lay = lay.filter(ImageFilter.MaxFilter(r * 2 + 1)).filter(ImageFilter.GaussianBlur(2))
    img.paste(Image.new("RGB", img.size, halo), (0, 0), lay.point(lambda v: min(255, int(v * 0.92))))
    ImageDraw.Draw(img).multiline_text(xy, text, font=f, fill=fill, anchor=anchor, spacing=6)


reg = R["by_region"]
CALL = [  # (lon, lat) of the text, all on open sea; text
    ((31.0, 44.5), f"ANATOLIA\n{reg['Anatolia']['n']} caravanserais:\nSeljuk hans and\nOttoman city khans"),
    ((47.32, 45.46), f"IRAN {reg['Iran']['n']}:\nSafavid\nand Qajar\nroads"),
    ((22.0, 34.6), f"LEVANT AND IRAQ {reg['Levant and Iraq']['n']}\nEGYPT AND ARABIA {reg['Egypt and Arabia']['n']}"),
    ((61.5, 22.9), f"SOUTH ASIA {reg['South Asia']['n']}:\nsarais of the Grand Trunk Road"),
]
for (lon, lat), t in CALL:
    x, y = px(lon, lat)
    halo_text((x, y), t, font("sb", 34), INKC_)

# ---- title band
d = ImageDraw.Draw(img)
d.text((60, 46), "Caravanserais of the Silk Roads", font=fr(96), fill=INKC_)
d.text((62, 172), f"{R['n']:,} roadside inns, city khans and ribats from Wikidata and OpenStreetMap, each drawn in ink and washed in the colour of its dynasty.",
       font=font("ser", 37), fill=INKC_)
d.text((62, 232), f"All together they stand a median {T['nn_median']:.0f} km apart. Taken one dynasty at a time, the Safavid caravanserais of Iran stand {T['saf_median']:.0f} km apart: a day's march.",
       font=font("seri", 37), fill=RED_)

# ---- bottom panel: legend (left), histogram (right)
y0p = TOP + MAPH + 40
d.text((60, y0p), "WHO BUILT IT: THE COURTYARD WASH", font=font("monom", 28), fill=RED_)
DY = [("early", "Before the Seljuks", "to c. 1040"), ("seljuk", "Seljuk", "c. 1040 to 1308"), ("ilkhanid", "Ilkhanid and Timurid", "c. 1256 to 1507"),
      ("mamluk", "Mamluk", "1250 to 1517"), ("ottoman", "Ottoman", "c. 1300 to 1922"), ("safavid", "Safavid", "1501 to 1736"),
      ("mughal", "Mughal and Suri", "1526 to 1857"), ("qajar", "Afsharid, Zand, Qajar", "1736 to 1925"), ("none", "Undated", "the plain majority")]
cnt = R["dates"]["by_dynasty"]
for i, (kk, lab, yrs) in enumerate(DY):
    col, row = i // 3, i % 3
    x = 60 + col * 540; y = y0p + 54 + row * 98
    s = Image.open(f"{SP}/inn-{kk}.png").convert("RGBA"); s = s.resize((int(s.width * 0.42), int(s.height * 0.42)), Image.LANCZOS)
    img.paste(s, (x, y), s)
    d.text((x + s.width + 18, y + 22), lab, font=font("ser", 30), fill=INKC_)
    d.text((x + s.width + 18, y + 58), f"{yrs} · {cnt.get(kk, 0):,} inns", font=font("mono", 22), fill=MUT)
# other symbols
x = 60 + 2 * 760 - 1520 + 760 * 0
oy = y0p + 54 + 3 * 98 + 10
items = [("urban-none", "Khan in a town or city"), ("ruin-none", "Mapped as a ruin"), ("ribat", "Ribat: a fort or lodge"), ("camels", None)]
xx = 60
for nm, lab in items[:3]:
    s = Image.open(f"{SP}/{nm}.png").convert("RGBA"); s = s.resize((int(s.width * 0.36), int(s.height * 0.36)), Image.LANCZOS)
    img.paste(s, (xx, oy + 4), s); d.text((xx + s.width + 12, oy + 26), lab, font=font("ser", 26), fill=INKC_)
    xx += s.width + 12 + int(d.textlength(lab, font=font("ser", 26))) + 34
# dashed link
ly = oy + 130
for t in range(0, 90, 18):
    d.line([(60 + t, ly), (60 + t + 10, ly)], fill=(140, 58, 30), width=5)
d.text((170, ly - 18), "Dashed lines join neighbouring stops (an inference from the inns, not mapped roads). Regions group modern countries.", font=font("ser", 27), fill=INKC_)

# histogram
hx, hy, hw, hh = 1700, y0p + 70, 1040, 430
d.text((hx, y0p), "DISTANCE TO THE NEAREST OTHER STOP", font=font("monom", 28), fill=RED_)
sp = R["spacing"]; bins = sp["hist_bins"]
nb = 24   # 0 to 120 km
def bars(key, col, top, h, lab):
    v = sp["hist"][key][:nb]; m = max(v)
    bw = hw / nb
    d.rectangle([hx + 30 / 120 * hw, top, hx + 40 / 120 * hw, top + h], fill=(232, 210, 160))
    for i, c in enumerate(v):
        bh = c / m * (h - 10)
        d.rectangle([hx + i * bw + 2, top + h - bh, hx + (i + 1) * bw - 2, top + h], fill=col, outline=INKC_, width=1)
    d.line([(hx, top + h), (hx + hw, top + h)], fill=INKC_, width=2)
    d.text((hx + hw * 0.5, top + 4), lab, font=font("sb", 27), fill=INKC_)
bars("all", (72, 60, 48), hy, 190, f"All {R['stages']['n']:,} stops: median {T['nn_median']:.0f} km")
bars("safavid", (62, 155, 166), hy + 240, 190, f"Safavid only ({T['saf_n']}): median {T['saf_median']:.0f} km")
for km in (0, 20, 40, 60, 80, 100, 120):
    xk = hx + km / 120 * hw
    d.text((xk, hy + 440), f"{km}", font=font("mono", 22), fill=MUT, anchor="ma")
d.text((hx + 35 / 120 * hw, hy + 474), "a day's march, 30 to 40 km (shaded)", font=font("seri", 24), fill=(122, 90, 30), anchor="ma")

# footer
fy = H - 64
d.line([(60, fy - 22), (W - 60, fy - 22)], fill=INKC_, width=2)
d.text((60, fy), "Data: Wikidata (CC0); © OpenStreetMap contributors (ODbL); Natural Earth. Base map: The Inked World (OpenStreetMap via OpenFreeMap, AWS Terrain Tiles, RESOLVE Ecoregions).",
       font=font("mono", 22), fill=MUT)
d.text((W - 60, fy - 60), "Dr Tristan Hotham · maps.tristanhotham.com/caravanserais", font=font("monom", 24), fill=INKC_, anchor="ra")
img.save(OUT, optimize=True)
print(OUT, img.size, os.path.getsize(OUT) // 1024, "KB")
