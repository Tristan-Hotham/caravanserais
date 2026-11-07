"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
Zenodo copies of files that also live elsewhere in the repo are hard links, so they take no extra disk."""
import re, shutil, zipfile, json as _json
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); B = f"{REL}/blog"; Z = f"{REL}/zenodo"
NAME = "Hotham_Caravanserais_of_the_Silk_Roads"
os.makedirs(B, exist_ok=True); os.makedirs(Z, exist_ok=True)


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f in (None, "raw"): return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f0": return f"{round(float(v))}"
    raise ValueError(f)


# blog figures
for src, dst in (("img/map_silk.jpg", "b_silk.jpg"), ("img/map_iran.jpg", "b_iran.jpg"), ("img/map_anatolia.jpg", "b_anatolia.jpg"),
                 ("img/fig_spacing.png", "b_spacing.png"), ("img/fig_dynasty.png", "b_dynasty.png")):
    shutil.copy(os.path.join(ROOT, src), f"{B}/{dst}")
# facts stated in words (alt text) in the blog
d = R["dates"]["by_dynasty"]
assert (d["safavid"], d["qajar"], d["ottoman"], d["seljuk"], d["none"]) == (97, 78, 70, 29, 642), d
assert R["heritage"]["anatolia_listed"] == 1   # "only 1 is listed"
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL)([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
for img in used:
    assert os.path.exists(f"{B}/{img}"), img
for fn in os.listdir(B):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{B}/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{B}/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Caravanserais of the Silk Roads: a day's march apart?",
        "slug": "caravanserais",
        "excerpt": f"{R['n']:,} caravanserais, khans and ribats from Wikidata and OpenStreetMap on a hand-inked map. All together they crowd closer than a day's march; one dynasty at a time, the Safavid caravanserais of Iran stand a median {round(R['text']['saf_median'])} km apart.",
        "seo_description": "A hand-inked map of the caravanserais of the Silk Roads from open data: where they are, how far apart they stand and who built them.",
        "tags": ["caravanserais", "Silk Roads", "Iran", "Anatolia", "Safavid", "Seljuk", "historical geography", "maps", "Wikidata", "OpenStreetMap"],
        "header_alt": f"Title card reading 'Caravanserais of the Silk Roads' in black and red on parchment, beside a hand-inked map of Anatolia and Iran dotted with tiny drawings of caravanserais. Text: {R['n']:,} caravanserais; Safavid ones stand {round(R['text']['saf_median'])} km apart, a day's march."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{B}/meta.json", indent=2)


# Zenodo
def link(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    os.link(src, dst)


link(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
for f in ("caravanserais.csv", "caravanserais.geojson", "routes_inferred.geojson", "results.json"):
    link(f"{DATA}/{f}", f"{Z}/{f}")
zp = f"{Z}/caravanserais_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for dname in ("code", "data", "js"):
        for fn in sorted(os.listdir(os.path.join(ROOT, dname))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, dname, fn), f"caravanserais/{dname}/{fn}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"caravanserais/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\emph{", "").replace("}", "").replace("\\&", "&")
zmeta = {"title": "Caravanserais of the Silk Roads: Where the Inns Were, How Far Apart, and Who Built Them",
         "upload_type": "publication", "publication_type": "workingpaper",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "description": f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/caravanserais/. Data and code: https://github.com/Tristan-Hotham/caravanserais.</p>"
                        "<p>Licences: text and figures CC BY 4.0; code MIT; data derived from OpenStreetMap ODbL 1.0 (© OpenStreetMap contributors); Wikidata content CC0.</p>",
         "keywords": ["caravanserai", "khan", "Silk Roads", "Safavid", "Seljuk", "Iran", "Anatolia", "historical geography", "Wikidata", "OpenStreetMap", "maps"],
         "license": "cc-by-4.0",
         "related_identifiers": [{"identifier": "https://github.com/Tristan-Hotham/caravanserais", "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": "https://maps.tristanhotham.com/caravanserais/", "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://doi.org/10.5281/zenodo.23860253", "relation": "references", "resource_type": "publication"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.openstreetmap.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}]}
jsave(zmeta, f"{Z}/metadata.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
print("blog words", words, "; zenodo files", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
