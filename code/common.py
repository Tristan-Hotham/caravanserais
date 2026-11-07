"""Shared paths and helpers for the caravanserais study.

Raw inputs (read only, never edited):
  RAW/caravanserai_wikidata.tsv     Wikidata items that are instances of caravanserai (Q186347), khan (Q115921107) or
                                    ribat (Q1333989) or their subclasses, with coordinates (queries/caravanserai_wikidata.rq)
  RAW/caravanserai_osm_tags.json    OpenStreetMap elements tagged historic/building/heritage:type/amenity=caravanserai
  RAW/caravanserai_osm_names_*.json OpenStreetMap name-search candidates (used only if present)
  GEO/ne_10m_admin_0_countries.geojson, ne_10m_populated_places_simple.geojson, ne_50m_land.geojson (Natural Earth)
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/home/claude/newdata/raw_new6/caravan"
GEO = "/home/claude/newdata/raw/geo"
DATA = os.path.join(ROOT, "data")
WORK = "/home/claude/work/new6/caravanserais/work"
FONTS = "/home/claude/ref/fonts"
INK = "/home/claude/studies/ink-map"          # sister project: the Inked World engine (read only)
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "caravanserais"
PAGE = "https://maps.tristanhotham.com/caravanserais/"
REPO = "https://github.com/Tristan-Hotham/caravanserais"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# the parchment palette of the Inked World (js/ink-palette.js)
PAPER = "#F3E5BF"; PAPER2 = "#FBF5E4"; INKC = "#2B2119"; RED = "#A3261B"; BLUE = "#3D6E9E"; MUTED = "#6E604E"; GOLD = "#B8862B"


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text taken from Wikidata and OpenStreetMap (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def hav(lon1, lat1, lon2, lat2):
    """Great-circle distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0088 * math.asin(min(1, math.sqrt(a)))
