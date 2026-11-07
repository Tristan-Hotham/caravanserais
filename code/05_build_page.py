"""Build index.html from code/page_template.html and data/results.json. 10.5281/zenodo.24043674 and https://blog.tristanhotham.com/2026/10/31/caravanserais/ stay for the publisher."""
import re
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "BLOG_URL", "DOI_URL"}


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
    if f == "f1": return f"{float(v):.1f}"
    raise ValueError(f)


def fill(t):
    def rep(m):
        k = m.group(1)
        if k in KEEP or k.startswith("TABLE_") or k in ("FULLSCREEN", "NAME_SEARCH_SENTENCE"):
            return m.group(0)
        return fmt(get(k), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, t)


# claims made in words in the page (the numbers themselves come from results.json)
T = R["text"]
assert "Çeşme" in " ".join(T["chain1"]["ends"]) and "Kavuncu Han" in T["chain1"]["ends"], "chain 1 is described as Çeşme to near Cizre"
assert "Lat Caravanserai" in T["chain2"]["ends"] and "Bahr-e Tork Caravanserai" in T["chain2"]["ends"], "chain 2 is described as Gilan to the Gulf"
assert R["n_ribat"] == 7 and R["dates"]["by_dynasty"]["safavid"] == max(v for k, v in R["dates"]["by_dynasty"].items() if k != "none")
assert len(R["dates"]["year_errors"]) == 3
assert R["by_region"]["South Asia"]["n"] < 30 and R["by_region"]["Central Asia and Afghanistan"]["n"] < 80
assert not any(c["country"] == "China" for c in R["by_country"])

t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
rows = ""
for reg in ["Anatolia", "Iran", "Caucasus", "Central Asia and Afghanistan", "Levant and Iraq", "Egypt and Arabia", "Balkans and Crimea", "South Asia", "Maghreb and Europe"]:
    b = R["by_region"][reg]
    rows += f"<tr><td>{reg}</td><td>{b['n']:,}</td><td>{b['roadside']:,}</td><td>{b['urban']:,}</td><td>{b['dated']:,}</td><td>{b['listed']:,}</td></tr>"
TBL = ('<table class="t"><thead><tr><th>Region</th><th>All</th><th>Roadside</th><th>In towns</th><th>Dated</th><th>Listed</th></tr></thead>'
       f"<tbody>{rows}</tbody></table>"
       '<p class="src">Regions group modern countries. All includes the seven ribats (forts and lodges) of the Maghreb and Iberia; the other columns count inns only.</p>')
nf = R["sources"]["name_files"]
if nf:
    k = sum(v for kk, v in R["sources"]["name_candidates"].items() if kk.startswith("kept"))
    NS = (f" A search of OpenStreetMap names for caravanserai, khan, han, ribat and their equivalents in other languages found "
          f"{R['sources']['name_candidates'].get('seen', 0):,} candidates; after filtering out mosques, tombs, bridges, places and the many other things called Khan or Han, "
          f"{k:,} were kept, and {R['sources']['osm_new_by_name']:,} of those were not already on the list.")
else:
    NS = (" A wider search of OpenStreetMap by name (khan, han, ribat and their equivalents) was planned but its results were not "
          "available for this version, so only features explicitly tagged as caravanserais are used.")
t = t.replace("{{TABLE_REGIONS}}", TBL).replace("{{NAME_SEARCH_SENTENCE}}", NS)
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("https://doi.org/10.5281/zenodo.24043674", "https://doi.org/10.5281/zenodo.24043674")
t = fill(t)
left = set(re.findall(r"\{\{([^}]+)\}\}", t))
assert left <= {"DOI", "BLOG_URL"}, left
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t), "bytes")
