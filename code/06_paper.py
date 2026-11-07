"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex."""
import re, shutil, subprocess
from collections import Counter
from common import *

R = jload(f"{DATA}/results.json"); C = jload(f"{WORK}/classified.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Caravanserais_of_the_Silk_Roads"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    return tex(str(v))


S = R["sources"]
assert "osm matched by distance and name (500 m)" not in jload(f"{WORK}/merge_summary.json")["match"], "paper says the 500 m rule added none"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sources and what was kept.}\\label{tab:sources}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.2cm}>{\\raggedright\\arraybackslash}p{6.4cm}r>{\\raggedright\\arraybackslash}p{2.2cm}}\\toprule Source & Kept & Records & Licence\\\\\\midrule\n"
      f"Wikidata & Caravanserais, khans and ribats with coordinates & {S['wd_n']:,} & CC0\\\\\n"
      f"OpenStreetMap & Features tagged as caravanserais (after merging duplicates) & {S['osm_after_dupes']:,} & ODbL 1.0\\\\\n"
      f"Merged & One record per building & {R['n']:,} & ODbL 1.0\\\\\n"
      "Natural Earth & Countries and populated places & & Public domain\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
STY = Counter(l for r in C if r["kind"] == "inn" for l in r["style_labels"])
DYNL = {"Anatolian Seljuk architecture": "Seljuk", "Seljuk architecture": "Seljuk", "Ilkhanid architecture": "Ilkhanid and Timurid", "Timurid architecture": "Ilkhanid and Timurid",
        "Safavid architecture": "Safavid", "Zand architecture": "Afsharid, Zand and Qajar", "Qajar architecture": "Afsharid, Zand and Qajar", "Ottoman architecture": "Ottoman",
        "Mamluk architecture": "Mamluk", "Mughal architecture": "Mughal and Suri", "Sasanian architecture": "Before the Seljuks", "Ziyarid architecture": "Before the Seljuks",
        "Ghaznavid architecture": "Before the Seljuks", "Pahlavi architecture": "Modern"}
rows = "".join(f"{tex(k)} & {DYNL.get(k, 'not used')} & {v:,}\\\\\n" for k, v in STY.most_common())
TST = ("\\begin{table}[tbp]\\centering\\small\\caption{Architectural styles of inns in Wikidata and the dynasty each implies.}\\label{tab:styles}"
       "\\begin{tabular}{llr}\\toprule Style (P149) & Dynasty & Inns\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for reg in ["Anatolia", "Iran", "Caucasus", "Central Asia and Afghanistan", "Levant and Iraq", "Egypt and Arabia", "Balkans and Crimea", "South Asia", "Maghreb and Europe"]:
    b = R["by_region"][reg]; s = R["spacing"]["by_region"][reg]
    rows += f"{reg} & {b['n']:,} & {b['roadside']:,} & {b['urban']:,} & {b['dated']:,} & {b['listed']:,} & {s.get('n', 0):,} & {(format(s['median'], '.1f') if s.get('n', 0) >= 3 else 'n/a')}\\\\\n"
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Records by region. Inn columns exclude the seven ribats; stops group inns within 3 km; the last column is the median distance to the nearest other stop (km).}\\label{tab:regions}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Region & All & Roadside & Urban & Dated & Listed & Stops & Median km\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
sp = R["spacing"]
L = [("All stops, nearest neighbour", sp["all_stages"]), ("Roadside stops only", sp["roadside_stages"]), ("Links of the spanning tree ($\\leq$ 80 km)", sp["route_edges"]),
     ("Safavid inns of Iran, same dynasty", sp["by_dynasty"]["safavid_iran"]), ("Afsharid, Zand and Qajar inns of Iran", sp["by_dynasty"]["qajar_iran"]),
     ("Seljuk inns of Anatolia", sp["by_dynasty"]["seljuk_anatolia"]), ("Ottoman roadside inns of Anatolia", sp["by_dynasty"]["ottoman_anatolia_roadside"])]
rows = "".join(f"{n} & {s['n']:,} & {s['median']:.1f} & {s['q1']:.1f} to {s['q3']:.1f} & {s['pc_30_40']:.1f} & {s['pc_20_50']:.1f}\\\\\n" for n, s in L)
TSP = ("\\begin{table}[tbp]\\centering\\small\\caption{Spacing of caravanserais (great-circle km).}\\label{tab:spacing}\\setlength{\\tabcolsep}{4pt}"
       "\\begin{tabular}{lrrrrr}\\toprule Measure & n & Median & Quartiles & \\% 30 to 40 & \\% 20 to 50\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("\\url{{{meta.page}}}", "\\url{%s}" % R["meta"]["page"]).replace("\\url{{{meta.repo}}}", "\\url{%s}" % R["meta"]["repo"])
t = t.replace("{{TABLE_SOURCES}}", TS).replace("{{TABLE_STYLES}}", TST).replace("{{TABLE_REGIONS}}", TR).replace("{{TABLE_SPACING}}", TSP)
t = re.sub(r"\{\{(?!DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3) or "raw"), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= {"DOI"}
assert "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
for f in ("fig_regions.png", "fig_spacing.png", "fig_dynasty.png", "fig_years.png", "map_iran.jpg", "map_anatolia.jpg"):
    shutil.copy(os.path.join(ROOT, "img", f), os.path.join(OUT, f))
# the DOI placeholder must survive LaTeX: compile a copy with the DOI from the environment (DOI=10.5281/zenodo.N python3
# code/06_paper.py) or a dummy, and keep 10.5281/zenodo.24043674 in the .tex for the publisher
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
open(os.path.join(OUT, "_build.tex"), "w", encoding="utf-8").write(t.replace("10.5281/zenodo.24043674", os.environ.get("DOI", "10.5281/zenodo.DOI")))
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "_build.tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, "_build.log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower()][:12])
shutil.move(os.path.join(OUT, "_build.pdf"), os.path.join(OUT, NAME + ".pdf"))
for fn in os.listdir(OUT):
    if fn.startswith("_build"): os.remove(os.path.join(OUT, fn))
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
