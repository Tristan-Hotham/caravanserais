"""Merge Wikidata and OpenStreetMap caravanserais into one deduplicated list (WORK/merged.json).

1. Wikidata items (CC0) with coordinates.
2. OpenStreetMap elements explicitly tagged as caravanserais (ODbL); matched to Wikidata through their wikidata=* tag,
   or, without one, to a Wikidata item within 150 m (or within 500 m when the names share a word).
   OpenStreetMap elements that duplicate each other (a node and a way for one building) are merged within 60 m.
3. OpenStreetMap name-search candidates (caravanserai_osm_names_*.json), if present: kept only when the name and tags pass
   the filters in name_candidate() below, and then deduplicated as in 2.
Every record gets a country from Natural Earth.
"""
import csv, glob, re
from collections import Counter, defaultdict
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

# ------------------------------------------------------------------ countries (Natural Earth 1:10m)
NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
GEOMS = [shape(f["geometry"]) for f in NE]
TREE = STRtree(GEOMS)
NAMES = [f["properties"]["NAME"] for f in NE]
ISO = [f["properties"]["ADM0_A3"] for f in NE]


def country(lon, lat):
    p = Point(lon, lat)
    for i in TREE.query(p):
        if GEOMS[i].contains(p):
            return ISO[i], NAMES[i]
    i = TREE.nearest(p)
    if GEOMS[i].distance(p) < 0.3:
        return ISO[i], NAMES[i]
    return None, None


def qid(s):
    return s.strip("<>\"").split("/")[-1]


def lit(s):
    """'"Name"@xx' -> ('Name', 'xx')"""
    m = re.match(r'^"?(.*?)"?@([a-z][\w-]*)$', s.strip(), re.S)
    return (m.group(1), m.group(2)) if m else (s.strip('"'), "")


# ------------------------------------------------------------------ 1. Wikidata
rows = list(csv.reader(open(f"{RAW}/caravanserai_wikidata.tsv", encoding="utf-8"), delimiter="\t"))
hdr, rows = rows[0], rows[1:]
WD, wd_nocoord = [], 0
for r in rows:
    m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", r[3])
    if not m:
        wd_nocoord += 1
        continue
    lon, lat = float(m.group(1)), float(m.group(2))
    en, _ = lit(r[1]) if r[1] else ("", "")
    nat, lang = lit(r[2]) if r[2] else ("", "")
    WD.append(dict(src="wikidata", qid=qid(r[0]), name=en or nat, name_native=nat if nat != en else "", name_lang=lang,
                   lon=lon, lat=lat, wd_country=qid(r[4]) if r[4] else "",
                   roots=[qid(x) for x in r[5].split("|") if x],
                   inception=int(r[6]) if r[6] else None, inception_precision=int(r[7]) if r[7] else None,
                   styles=sorted({qid(x) for x in r[8].split("|") if x}), heritage=sorted({qid(x) for x in r[9].split("|") if x}),
                   sitelinks=int(r[10]) if r[10] else 0, enwiki=r[11].strip("<>") if r[11] else "",
                   osm=[], osm_tags={}))
wd_rows = len(rows)
by_qid = {w["qid"]: w for w in WD}
assert len(by_qid) == len(WD)

# ------------------------------------------------------------------ 2. OpenStreetMap, explicit tags
def osm_point(e):
    if "center" in e:
        return e["center"]["lon"], e["center"]["lat"]
    return e["lon"], e["lat"]


def osm_rec(e, how):
    lon, lat = osm_point(e)
    t = e.get("tags", {})
    return dict(src="osm", how=how, osm=[f"{e['type']}/{e['id']}"], lon=lon, lat=lat, name=t.get("name:en") or t.get("name") or "",
                name_native=t.get("name", "") if t.get("name:en") and t.get("name") != t.get("name:en") else "",
                qid_tag=t.get("wikidata", ""), osm_tags={k: t[k] for k in ("historic", "building", "ruins", "tourism", "heritage", "start_date", "historic:civilization", "amenity") if k in t})


def words(s):
    w = set(norm(s).split())
    return {x for x in w if len(x) > 2 and x not in {"han", "hani", "khan", "caravanserai", "kervansarayi", "kervansaray", "caravansary", "the", "of", "and", "karvansaray", "caravanserail", "karawanserei"}}


tags_raw = jload(f"{RAW}/caravanserai_osm_tags.json")["elements"]
OSM = [osm_rec(e, "tag") for e in tags_raw]

# name-search candidates (if they have arrived)
NAME_FILES = sorted(glob.glob(f"{RAW}/caravanserai_osm_names_*.json"))
STRONG = re.compile(r"caravan|karavan|karvan|kervan|carvan|karwan|کاروان|کاروانسرا|караван|քարավան|კარავან|caravansar|caravanser", re.I)
HAN = re.compile(r"(^|\s)(han|hanı|hani|khan|xan|hán|ан|хан|خان)(\s|$)", re.I)
RIBAT = re.compile(r"ribat|robat|rabat|رباط|rباط", re.I)
FUNDUQ = re.compile(r"funduq|fondouk|fonduk|fondaco|foundouk|وكالة|wikala|wakala|okel|فندق", re.I)
NOT_INN = re.compile(r"mosque|masjid|cami|camii|mescit|türbe|turbe|tomb|mausole|kümbet|kumbet|madrasa|medrese|madrese|bath|hamam|hammam|"
                     r"bridge|köprü|kopru|castle|kale|qala|church|kilise|fountain|çeşme|cesme|school|palace|saray(ı|i)? ?$|cemetery|mezar|"
                     r"آرامگاه|مقبره|مسجد|امامزاده|قلعه|حمام|مدرسه|گنبد|"
                     r"مزار|جامع|ضريح|قبر|zaviye|tekke|zawiya|زاوية|imamzadeh|shrine", re.I)
HAN_LANDS = {"TUR", "CYP", "CYN", "BGR", "GRC", "MKD", "SRB", "BIH", "ALB", "KOS", "MNE", "HRV", "ROU", "UKR", "SYR", "LBN", "ISR", "PSX", "JOR", "IRQ", "EGY", "AZE", "ARM", "GEO", "SAU", "KWT"}
ROBAT_LANDS = {"IRN", "AFG", "TKM", "UZB", "TJK", "KGZ", "KAZ", "PAK"}
cand_stats = Counter()


def name_candidate(e):
    """Decide whether an OpenStreetMap name-search hit is a caravanserai. Returns (keep, reason)."""
    t = e.get("tags", {})
    name = " ".join(t.get(k, "") for k in ("name", "name:en", "name:tr", "name:fa", "name:ar", "alt_name", "old_name"))
    if t.get("historic") == "caravanserai" or t.get("building") == "caravanserai":
        return True, "tag"
    if not (t.get("historic") or t.get("ruins") or t.get("building") or t.get("heritage")):
        return False, "no historic, ruins, building or heritage tag"
    if t.get("place") or t.get("highway") or t.get("shop") or t.get("tourism") == "caravan_site":
        return False, "a place, road, shop or campsite"
    if NOT_INN.search(name) and not STRONG.search(name):
        return False, "another kind of building"
    lon, lat = osm_point(e)
    iso, _ = country(lon, lat)
    if STRONG.search(name):
        return True, "caravanserai word"
    if FUNDUQ.search(name) and iso in {"EGY", "MAR", "TUN", "DZA", "LBY", "ITA", "SYR", "LBN", "ISR", "PSX", "IRQ"}:
        return True, "funduq or wikala"
    if RIBAT.search(name) and iso in ROBAT_LANDS:
        return True, "robat in Iran or Central Asia"
    if HAN.search(name) and iso in HAN_LANDS and t.get("historic") not in ("memorial", "monument", "wayside_shrine", "tomb", "city_gate"):
        if re.search(r"younis|yunis|yunus", name, re.I):
            return False, "Khan Younis"
        return True, "han or khan in the Ottoman lands"
    return False, "ambiguous word outside its region"


for fn in NAME_FILES:
    els = jload(fn).get("elements", [])
    for e in els:
        if "tags" not in e or not ("center" in e or "lat" in e):
            continue
        cand_stats["seen"] += 1
        keep, why = name_candidate(e)
        cand_stats[("kept: " if keep else "dropped: ") + why] += 1
        if keep:
            OSM.append(osm_rec(e, "name"))

# OSM-OSM duplicates (same element listed twice, or a node and a way for one building): within 60 m
seen, osm_u = {}, []
for o in OSM:
    k = o["osm"][0]
    if k in seen:
        continue
    seen[k] = 1
    osm_u.append(o)
OSM = osm_u
OSM.sort(key=lambda o: ({"relation": 0, "way": 1, "node": 2}[o["osm"][0].split("/")[0]], o["how"] != "tag"))
merged_osm = []
for o in OSM:
    dup = None
    for m in merged_osm:
        if abs(m["lat"] - o["lat"]) < 0.002 and hav(m["lon"], m["lat"], o["lon"], o["lat"]) < 0.06 and \
                (not o["qid_tag"] or not m["qid_tag"] or o["qid_tag"] == m["qid_tag"]):
            dup = m
            break
    if dup:
        dup["osm"] += o["osm"]
        dup["qid_tag"] = dup["qid_tag"] or o["qid_tag"]
        dup["name"] = dup["name"] or o["name"]
    else:
        merged_osm.append(o)
osm_dupes = len(OSM) - len(merged_osm)

# match to Wikidata
stats = Counter()
LATI = defaultdict(list)
for w in WD:
    LATI[int(w["lat"] * 10)].append(w)


def near_wd(o, r_km):
    out = []
    for k in range(int(o["lat"] * 10) - 1, int(o["lat"] * 10) + 2):
        for w in LATI[k]:
            d = hav(w["lon"], w["lat"], o["lon"], o["lat"])
            if d <= r_km:
                out.append((d, w))
    return sorted(out, key=lambda x: x[0])


ALL = list(WD)
for o in merged_osm:
    w = None
    if o["qid_tag"] in by_qid:
        w = by_qid[o["qid_tag"]]
        stats["osm matched by wikidata tag"] += 1
    else:
        cands = [(d, x) for d, x in near_wd(o, 0.5) if not x["osm"]]
        if cands and cands[0][0] <= 0.15:
            w = cands[0][1]; stats["osm matched by distance (150 m)"] += 1
        else:
            for d, x in cands:
                if words(o["name"]) & (words(x["name"]) | words(x["name_native"])):
                    w = x; stats["osm matched by distance and name (500 m)"] += 1
                    break
    if w is not None:
        w["osm"] += o["osm"]
        w["osm_tags"] = w["osm_tags"] or o["osm_tags"]
        w["osm_lonlat"] = [o["lon"], o["lat"]]
        w["osm_how"] = o["how"]
    else:
        o["qid"] = o.pop("qid_tag") or ""
        stats[f"osm new ({o['how']})"] += 1
        ALL.append(o)

for i, r in enumerate(ALL):
    r.pop("qid_tag", None)
    r["id"] = r["qid"] if r.get("qid") else r["osm"][0].replace("/", "_")
    r["iso"], r["country"] = country(r["lon"], r["lat"])
    r["n_osm"] = len(r["osm"])
ids = [r["id"] for r in ALL]
assert len(ids) == len(set(ids))

summary = dict(wd_rows=wd_rows, wd_nocoord=wd_nocoord, wd_n=len(WD), osm_tag_n=len(tags_raw), osm_after_dupes=len(merged_osm),
               osm_dupes=osm_dupes, name_files=[os.path.basename(f) for f in NAME_FILES], name_candidates=dict(cand_stats),
               match=dict(stats), merged_n=len(ALL), wd_with_osm=sum(1 for r in WD if r["osm"]),
               no_country=sum(1 for r in ALL if not r["iso"]))
jsave(ALL, f"{WORK}/merged.json")
jsave(summary, f"{WORK}/merge_summary.json", indent=1)
print(json.dumps(summary, indent=1, ensure_ascii=False))
print(Counter(r["country"] for r in ALL).most_common(40))
