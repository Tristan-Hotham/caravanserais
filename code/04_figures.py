"""Charts for the page, paper and blog, drawn on parchment in the Inked World palette (img/fig_*.png)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np
from common import *

for f in os.listdir(FONTS):
    if f.endswith(".ttf"):
        fm.fontManager.addfont(os.path.join(FONTS, f))
plt.rcParams.update({"font.family": "Source Serif 4", "font.weight": "normal", "font.size": 11, "axes.edgecolor": INKC, "axes.labelcolor": INKC, "xtick.color": INKC,
                     "ytick.color": INKC, "text.color": INKC, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "savefig.facecolor": PAPER})
R = jload(f"{DATA}/results.json")
IMG = os.path.join(ROOT, "img"); os.makedirs(IMG, exist_ok=True)
DYNC = {"early": "#8A6A4E", "seljuk": "#B4472E", "ilkhanid": "#5C7896", "mamluk": "#C9A24A", "ottoman": "#6E8A50", "safavid": "#3E9BA6",
        "mughal": "#D08A4A", "qajar": "#C27597", "modern": "#9A958A", "other": "#B9AC88", "none": "#E7D2A0"}
DLAB = {"early": "Before the Seljuks", "seljuk": "Seljuk", "ilkhanid": "Ilkhanid and Timurid", "mamluk": "Mamluk", "ottoman": "Ottoman",
        "safavid": "Safavid", "mughal": "Mughal and Suri", "qajar": "Afsharid, Zand and Qajar", "modern": "Modern", "other": "Other or regional", "none": "Undated"}


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=3)


def title(fig, t, sub):
    fig.text(0.012, 0.975, t, fontsize=17, va="top", family="Fraunces", fontweight=900)
    fig.text(0.012, 0.905, sub, fontsize=11, va="top", color=MUTED)


# ---- spacing: all stops vs Safavid only
sp = R["spacing"]; bins = sp["hist_bins"]
fig, axs = plt.subplots(1, 2, figsize=(10, 4.4), sharey=False)
for ax, key, lab, col, med in ((axs[0], "all", f"All {R['stages']['n']:,} stops", INKC, R["text"]["nn_median"]),
                               (axs[1], "safavid", f"Safavid caravanserais of Iran ({R['text']['saf_n']})", "#3E9BA6", R["text"]["saf_median"])):
    h = sp["hist"][key]
    ax.axvspan(30, 40, color=GOLD, alpha=0.22, lw=0)
    ax.bar(np.array(bins[:-1]) + 2.5, h, width=4.3, color=col, alpha=0.85, edgecolor=INKC, lw=0.6)
    ax.axvline(med, color=RED, lw=1.6, ls=(0, (4, 2)))
    ax.text(med + 2, max(h) * 0.97, f"median {round(med)} km", color=RED, fontsize=10.5, va="top")
    ax.set_xlim(0, 150); ax.set_xlabel("km to the nearest other stop"); ax.set_title(lab, loc="left", fontsize=12)
    style(ax)
axs[0].set_ylabel("stops")
axs[1].text(41, max(sp["hist"]["safavid"]) * 0.82, "a day's march\n(30 to 40 km)", ha="left", fontsize=9.5, color="#7A5A1E", style="italic")
fig.subplots_adjust(top=0.8, bottom=0.14, left=0.07, right=0.98, wspace=0.18)
title(fig, "How far apart the caravanserais stand", "All together they crowd closer than a day's march; one dynasty alone keeps the old rhythm")
fig.savefig(f"{IMG}/fig_spacing.png", dpi=160); plt.close(fig)

# ---- dynasties by region
REG = ["Anatolia", "Iran", "Caucasus", "Central Asia and Afghanistan", "Levant and Iraq", "Egypt and Arabia", "Balkans and Crimea", "South Asia", "Maghreb and Europe"]
RC = ["#B4472E", "#3E9BA6", "#6E8A50", "#C9A24A", "#5C7896", "#D08A4A", "#C27597", "#8A6A4E", "#9A958A"]
dyn = [k for k in DLAB if R["dates"]["by_dynasty"].get(k, 0) > 0]
dyn = sorted([k for k in dyn if k != "none"], key=lambda k: -R["dates"]["by_dynasty"][k]) + ["none"]
fig, ax = plt.subplots(figsize=(10, 5.2))
y = np.arange(len(dyn))[::-1]
left = np.zeros(len(dyn))
for reg, c in zip(REG, RC):
    v = np.array([R["dates"]["by_dynasty_region"][k].get(reg, 0) for k in dyn])
    if v.sum():
        ax.barh(y, v, left=left, color=c, edgecolor=INKC, lw=0.5, label=reg, height=0.68)
        left += v
for yy, k in zip(y, dyn):
    ax.text(left[list(dyn).index(k)] + 6, yy, f"{R['dates']['by_dynasty'][k]:,}", va="center", fontsize=10)
ax.set_yticks(y); ax.set_yticklabels([DLAB[k] for k in dyn]); ax.set_xlabel("inns")
ax.legend(frameon=False, fontsize=9, loc="center right", bbox_to_anchor=(1.0, 0.52), ncol=2)
style(ax)
fig.subplots_adjust(top=0.84, bottom=0.11, left=0.2, right=0.98)
title(fig, "Who built them", f"{R['dates']['n_dated']:,} of {R['n_inn']:,} inns have a dynasty in the data, nearly all from their architectural style")
fig.savefig(f"{IMG}/fig_dynasty.png", dpi=160); plt.close(fig)

# ---- dated years (paper): a strip of every inn with a building year, coloured by dynasty
C = jload(f"{WORK}/classified.json")
yrs = [(r["year"], r["dynasty"]) for r in C if r["kind"] == "inn" and r["year"]]
fig, ax = plt.subplots(figsize=(10, 2.6))
rng = np.random.default_rng(3)
for yv, d in yrs:
    ax.scatter(yv, rng.uniform(-1, 1), s=46, color=DYNC[d], edgecolor=INKC, lw=0.6, zorder=3)
ax.set_yticks([]); ax.set_xlim(1000, 1925); ax.set_ylim(-1.6, 1.6); style(ax); ax.spines["left"].set_visible(False)
ax.set_xlabel("year of building (a century given alone is drawn at its middle)")
fig.subplots_adjust(top=0.7, bottom=0.24, left=0.02, right=0.98)
title(fig, f"The {len(yrs)} inns with a year", "Coloured by dynasty, as on the map")
fig.savefig(f"{IMG}/fig_years.png", dpi=160); plt.close(fig)

# ---- regions table as chart (paper): all, roadside, urban, dated, listed
fig, ax = plt.subplots(figsize=(10, 4.2))
x = np.arange(len(REG)); w = 0.26
b = R["by_region"]
ax.bar(x - w, [b[r]["n"] for r in REG], w, color=INKC, label="all")
ax.bar(x, [b[r]["dated"] for r in REG], w, color=RED, label="dated")
ax.bar(x + w, [b[r]["listed"] for r in REG], w, color=BLUE, label="heritage listed")
ax.set_xticks(x); ax.set_xticklabels([r.replace(" and ", "\nand ") for r in REG], fontsize=8.6)
ax.legend(frameon=False); style(ax)
fig.subplots_adjust(top=0.82, bottom=0.17, left=0.06, right=0.99)
title(fig, "The record by region", "Iran is dated and listed; Anatolia is mapped but rarely dated or listed in Wikidata")
fig.savefig(f"{IMG}/fig_regions.png", dpi=160); plt.close(fig)
print(sorted(os.listdir(IMG)))
