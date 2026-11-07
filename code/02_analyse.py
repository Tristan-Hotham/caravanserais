"""Classify the merged caravanserais, date them by dynasty, group them into stages, measure the spacing and infer the chains.

Outputs: data/caravanserais.csv, data/caravanserais.geojson, data/routes_inferred.geojson, WORK/analysis.json
"""
import csv, math, re
from collections import Counter, defaultdict
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import minimum_spanning_tree, connected_components
from common import *

A = jload(f"{WORK}/merged.json")
PP = [f["properties"] for f in jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]]

# ------------------------------------------------------------------ regions
REGION = {}
for iso in ("TUR", "CYN", "CYP"): REGION[iso] = "Anatolia"
REGION["IRN"] = "Iran"
for iso in ("AZE", "ARM", "GEO"): REGION[iso] = "Caucasus"
for iso in ("GRC", "MKD", "BGR", "SRB", "BIH", "HRV", "ROU", "ALB", "KOS", "MNE", "UKR", "RUS"): REGION[iso] = "Balkans and Crimea"
for iso in ("SYR", "LBN", "ISR", "PSX", "JOR", "IRQ"): REGION[iso] = "Levant and Iraq"
for iso in ("EGY", "SAU", "YEM", "OMN", "ARE", "KWT", "QAT", "BHR"): REGION[iso] = "Egypt and Arabia"
for iso in ("AFG", "UZB", "TKM", "KAZ", "TJK", "KGZ", "CHN", "MNG"): REGION[iso] = "Central Asia and Afghanistan"
for iso in ("IND", "PAK", "BGD", "NPL"): REGION[iso] = "South Asia"
for iso in ("TUN", "MAR", "DZA", "LBY", "PRT", "ESP", "ITA", "FRA"): REGION[iso] = "Maghreb and Europe"
REGIONS = ["Anatolia", "Iran", "Caucasus", "Central Asia and Afghanistan", "Levant and Iraq", "Egypt and Arabia", "Balkans and Crimea", "South Asia", "Maghreb and Europe"]
COUNTRY_FIX = {"RUS": "Crimea", "N. Cyprus": "Northern Cyprus", "Bosnia and Herz.": "Bosnia and Herzegovina"}

# ------------------------------------------------------------------ styles and dynasties
STYLE = {"Q127632740": ("Anatolian Seljuk architecture", "seljuk"), "Q7448523": ("Seljuk architecture", "seljuk"),
         "Q98399895": ("Ilkhanid architecture", "ilkhanid"), "Q16047695": ("Timurid architecture", "ilkhanid"),
         "Q5957125": ("Safavid architecture", "safavid"), "Q5679012": ("Zand architecture", "qajar"), "Q5718239": ("Qajar architecture", "qajar"),
         "Q527449": ("Ottoman architecture", "ottoman"), "Q16210807": ("Mamluk architecture", "mamluk"), "Q542261": ("Mughal architecture", "mughal"),
         "Q3844828": ("Sasanian architecture", "early"), "Q98417627": ("Ziyarid architecture", "early"), "Q98400041": ("Ghaznavid architecture", "early"),
         "Q17993891": ("Pahlavi architecture", "modern"),
         "Q16414661": ("Shirvan-Absheron school", None), "Q212940": ("Islamic architecture", None), "Q1501585": ("architecture of Iran", None),
         "Q54111": ("Neoclassical architecture", None), "Q74156": ("Moorish Revival architecture", None), "Q1295040": ("Art Nouveau", None),
         "Q12228302": ("Damascene architecture", None), "Q47591": ("Byzantine architecture", None)}
DYN = [  # key, label, years (for the text), colour on the page
    ("early", "Before the Seljuks", "before about 1040"),
    ("seljuk", "Seljuk", "about 1040 to 1308"),
    ("ilkhanid", "Ilkhanid and Timurid", "about 1256 to 1507"),
    ("mamluk", "Mamluk", "1250 to 1517"),
    ("ottoman", "Ottoman", "about 1300 to 1922"),
    ("safavid", "Safavid", "1501 to 1736"),
    ("mughal", "Mughal and Suri", "1526 to 1857"),
    ("qajar", "Afsharid, Zand and Qajar", "1736 to 1925"),
    ("modern", "Modern", "after 1925"),
    ("other", "Other or regional", ""),
    ("none", "Undated", ""),
]
DYN_LABEL = {k: l for k, l, _ in DYN}
DYN_ORDER = [k for k, _, _ in DYN]
HERIT = {"Q5958900": "Iranian National Heritage", "Q43113623": "part of a UNESCO World Heritage Site", "Q9259": "UNESCO World Heritage Site",
         "Q26884649": "cultural heritage monument in Armenia", "Q916620": "Historic Monument", "Q10296658": "cultural heritage site in Ukraine",
         "Q45301843": "architectural monument of national significance of Ukraine", "Q3323436": "Immovable Cultural Heritage of Exceptional Importance"}
RIBAT_FORT = {"Q3430097", "Q48816409", "Q18716362", "Q60574216", "Q17390062", "Q4785449", "Q5836226"}  # Monastir, Sousse, Lamta, Sidi Khanfir, Arrifana, Alto da Vigia, San Sebastian (Granada)


def eff_year(y, p):
    """Usable building year from a Wikidata inception: year or decade as given, century as its midpoint (Wikidata writes the
    13th century as 1300 or 1201), millennium or coarser not used. Years before 300 and after 1925 are not taken as
    building dates (an error and museum openings, checked by hand)."""
    if y is None or p is None or p < 7:
        return None, "none" if y is None else "too coarse"
    if p == 7:
        c = math.ceil(y / 100)
        y = (c - 1) * 100 + 50
    if y < 300 or y > 1925:
        return None, "not a building date"
    return y, ("century" if p == 7 else "decade" if p == 8 else "year")


def dyn_from_year(y, region, iso):
    if y is None:
        return None
    if y >= 1925: return "modern"
    if region in ("Iran", "Central Asia and Afghanistan", "Caucasus"):
        if y < 1040: return "early"
        if y < 1220: return "seljuk"
        if y < 1501: return "ilkhanid" if region != "Caucasus" or y >= 1256 else "other"
        if y < 1736: return "safavid" if region != "Central Asia and Afghanistan" else "other"
        return "qajar" if region != "Central Asia and Afghanistan" else "other"
    if region == "Anatolia":
        if y < 1075: return "early"
        if y < 1308: return "seljuk"
        return "ottoman"
    if region == "Balkans and Crimea":
        return "ottoman" if 1360 <= y < 1913 else "other"
    if region in ("Levant and Iraq", "Egypt and Arabia"):
        if iso == "IRQ" and 1256 <= y < 1411: return "ilkhanid"   # Ilkhanid and Jalayirid Baghdad (Khan Murjan, 1359)
        if 1250 <= y < 1517: return "mamluk"
        if 1517 <= y < 1918: return "ottoman"
        return "other"
    if region == "South Asia":
        return "mughal" if 1526 <= y < 1858 else "other"
    return "other"


# ------------------------------------------------------------------ classify
PPA = np.array([[p["longitude"], p["latitude"], p["pop_max"]] for p in PP if p["pop_max"] >= 50000])
pp_tree = cKDTree(PPA[:, :2])
XY = np.array([[r["lon"], r["lat"]] for r in A])
tree = cKDTree(XY)
RUIN = re.compile(r"ruin|ویرانه|harabe|خرابه|أطلال", re.I)
REUSE = re.compile(r"hotel|هتل|اقامتگاه|بومگردی|guest ?house|motel|museum|موزه|restaurant|سفره ?خانه|رستوران", re.I)
for i, r in enumerate(A):
    # a few Wikidata labels are bot descriptions ("... (arkiyolohiyang dapit sa Isfahan, lat 33.49, long 51.76)"): keep the name only
    for k in ("name", "name_native"):
        r[k] = re.sub(r"\s*\([^)]*(lat \d|arkiyolohiyang|long \d)[^)]*\)", "", r.get(k) or "").strip()
    if r["name_native"] == r["name"]:
        r["name_native"] = ""
    r["region"] = REGION.get(r["iso"], "Other")
    r["country"] = COUNTRY_FIX.get(r["iso"], COUNTRY_FIX.get(r["country"], r["country"]))
    # kind
    if r.get("qid") in RIBAT_FORT:
        r["kind"] = "ribat"
    else:
        r["kind"] = "inn"
    # setting: urban if it sits in a cluster (two or more others within 1 km) or near the centre of a town or city of 50,000+
    # (within 2 km; 3 km for 200,000+; 5 km for a million+, Natural Earth populated places)
    near = [j for j in tree.query_ball_point(XY[i], 0.02) if j != i and hav(*XY[i], *XY[j]) <= 1.0]
    city = None
    for j in pp_tree.query_ball_point(XY[i], 0.08):
        lon, lat, pop = PPA[j]
        rad = 5.0 if pop >= 1e6 else 3.0 if pop >= 2e5 else 2.0
        if hav(r["lon"], r["lat"], lon, lat) <= rad:
            city = True
    r["urban"] = bool(len(near) >= 2 or city)
    r["setting"] = "ribat" if r["kind"] == "ribat" else ("urban" if r["urban"] else "roadside")
    # dates
    y, how = eff_year(r.get("inception"), r.get("inception_precision"))
    r["year"] = y; r["year_how"] = how
    sty = [s for s in r.get("styles", []) if s in STYLE]
    r["style_labels"] = [STYLE[s][0] for s in sty]
    ds = [STYLE[s][1] for s in sty if STYLE[s][1]]
    ds = sorted(set(ds), key=DYN_ORDER.index)
    dy = dyn_from_year(y, r["region"], r["iso"])
    if ds and dy:
        r["dynasty"] = ds[0]; r["dated_by"] = "style and year"
    elif ds:
        r["dynasty"] = ds[0]; r["dated_by"] = "style"
    elif dy:
        r["dynasty"] = dy; r["dated_by"] = "year"
    else:
        r["dynasty"] = "none"; r["dated_by"] = ""
    r["style_year_conflict"] = bool(ds and dy and dy not in ds and dy != "other")
    # heritage and survival
    h = r.get("heritage", [])
    r["heritage_labels"] = [HERIT.get(x, "national or regional heritage listing") for x in h]
    r["whs"] = any(x in ("Q43113623", "Q9259") for x in h)
    r["listed"] = bool(h) or bool(r.get("osm_tags", {}).get("heritage"))
    t = r.get("osm_tags", {})
    nm = " ".join([r.get("name", ""), r.get("name_native", "")])
    r["ruin"] = bool(t.get("ruins") in ("yes", "caravanserai", "caravansarai") or t.get("historic") == "ruins" or RUIN.search(nm))
    r["reuse"] = bool(t.get("tourism") in ("hotel", "guest_house", "motel", "hostel", "museum") or REUSE.search(nm))

# ------------------------------------------------------------------ stages: inns within 3 km of each other are one stop
inn = [r for r in A if r["kind"] == "inn"]
P = np.array([[r["lon"], r["lat"]] for r in inn])
# equirectangular km about each point is close enough at 3 km; use a projected copy for the trees
lat0 = 35.0
def proj(lon, lat):
    return np.c_[np.radians(lon) * 6371.0 * math.cos(math.radians(lat0)), np.radians(lat) * 6371.0]
Q = proj(P[:, 0], P[:, 1])
t2 = cKDTree(Q)
pairs = [(i, j) for i, j in t2.query_pairs(8.0) if hav(*P[i], *P[j]) <= 3.0]
n = len(inn)
g = coo_matrix((np.ones(len(pairs)), ([a for a, _ in pairs], [b for _, b in pairs])), shape=(n, n))
nc, lab = connected_components(g, directed=False)
stages = []
for c in range(nc):
    idx = np.where(lab == c)[0]
    lon, lat = P[idx, 0].mean(), P[idx, 1].mean()
    members = [inn[i] for i in idx]
    if len(idx) >= 4:   # four or more inns linked within 3 km of each other: a town's khan quarter
        for m in members:
            m["urban"] = True; m["setting"] = "urban"
    reg = Counter(m["region"] for m in members).most_common(1)[0][0]
    stages.append(dict(id=c, lon=float(lon), lat=float(lat), n=len(idx), region=reg, urban=any(m["urban"] for m in members),
                       name=max(members, key=lambda m: (m.get("sitelinks", 0), bool(m["name"])))["name"]))
    for m in members:
        m["stage"] = c
S = np.array([[s["lon"], s["lat"]] for s in stages])
SQ = proj(S[:, 0], S[:, 1])
st = cKDTree(SQ)
dd, ii = st.query(SQ, k=2)
for k, s in enumerate(stages):
    j = int(ii[k, 1])
    s["nn_km"] = round(hav(s["lon"], s["lat"], *S[j]), 2)
    s["nn"] = j

# minimum spanning tree over stages (from the 10 nearest neighbours of each), km on the sphere
dd, ii = st.query(SQ, k=min(11, len(stages)))
rows_, cols_, w_ = [], [], []
for a in range(len(stages)):
    for b in ii[a, 1:]:
        b = int(b)
        rows_.append(a); cols_.append(b); w_.append(hav(*S[a], *S[b]))
M = coo_matrix((w_, (rows_, cols_)), shape=(len(stages), len(stages))).tocsr()
M = M.maximum(M.T)
T = minimum_spanning_tree(M).tocoo()
edges = sorted([(int(a), int(b), float(w)) for a, b, w in zip(T.row, T.col, T.data)], key=lambda e: e[2])

# inferred routes: MST edges up to ROUTE_MAX km (about two days' march); longer gaps are left open
ROUTE_MAX = 80.0
route_edges = [e for e in edges if e[2] <= ROUTE_MAX]
gr = coo_matrix((np.ones(len(route_edges)), ([a for a, _, _ in route_edges], [b for _, b, _ in route_edges])), shape=(len(stages), len(stages)))
ncomp, clab = connected_components(gr, directed=False)
comp = Counter(clab)
chains = []
for c, cnt in comp.most_common():
    if cnt < 3:
        continue
    idx = [k for k in range(len(stages)) if clab[k] == c]
    km = sum(w for a, b, w in route_edges if clab[a] == c)
    regs = Counter(stages[k]["region"] for k in idx).most_common()
    # the two stages farthest apart in the chain (by straight line), as its ends
    pts = S[idx]
    far = max(((x, y) for x in range(len(idx)) for y in range(x + 1, len(idx))), key=lambda xy: hav(*pts[xy[0]], *pts[xy[1]])) if len(idx) > 1 else (0, 0)
    chains.append(dict(stages=cnt, inns=sum(stages[k]["n"] for k in idx), km=round(km), region=regs[0][0],
                       ends=[stages[idx[far[0]]]["name"], stages[idx[far[1]]]["name"]],
                       span_km=round(hav(*pts[far[0]], *pts[far[1]]))))

# ------------------------------------------------------------------ spacing statistics
def spacing(vals):
    v = np.array(sorted(vals))
    if not len(v):
        return {}
    return dict(n=int(len(v)), median=round(float(np.median(v)), 1), q1=round(float(np.percentile(v, 25)), 1), q3=round(float(np.percentile(v, 75)), 1),
                mean=round(float(v.mean()), 1),
                pc_30_40=round(100 * float(((v >= 30) & (v <= 40)).mean()), 1),
                pc_20_50=round(100 * float(((v >= 20) & (v <= 50)).mean()), 1),
                pc_under_20=round(100 * float((v < 20).mean()), 1), pc_over_50=round(100 * float((v > 50).mean()), 1))

nn_all = [s["nn_km"] for s in stages]
rural = [s for s in stages if not s["urban"]]
sp = dict(all_stages=spacing(nn_all), roadside_stages=spacing([s["nn_km"] for s in rural]),
          mst_edges=spacing([w for _, _, w in edges]), route_edges=spacing([w for _, _, w in route_edges]))
sp["by_region"] = {R: spacing([s["nn_km"] for s in stages if s["region"] == R]) for R in REGIONS}
sp["roadside_by_region"] = {R: spacing([s["nn_km"] for s in rural if s["region"] == R]) for R in REGIONS}
sp["route_by_region"] = {R: spacing([w for a, b, w in route_edges if stages[a]["region"] == R]) for R in REGIONS}
# histogram of nearest-neighbour gaps, 5 km bins to 150 km
bins = list(range(0, 155, 5))
hist = {}
for key, vals in (("all", nn_all), ("Iran", [s["nn_km"] for s in stages if s["region"] == "Iran"]), ("Anatolia", [s["nn_km"] for s in stages if s["region"] == "Anatolia"]),
                  ("route", [w for _, _, w in route_edges])):
    h, _ = np.histogram(np.clip(vals, 0, 149.99), bins=bins)
    hist[key] = [int(x) for x in h]
sp["hist_bins"] = bins
sp["hist"] = hist
sp["n_over_150"] = int(sum(1 for v in nn_all if v >= 150))


# one dynasty at a time: the gap from each inn to the nearest other inn of the same dynasty (more than 3 km away, so
# inns in the same stop do not count). Later builders filled gaps and doubled roads; one generation alone shows its own rhythm.
def nn_same(rs):
    pts = [(r["lon"], r["lat"]) for r in rs]
    out = []
    for i, p in enumerate(pts):
        d = [hav(*p, *q) for j, q in enumerate(pts) if j != i]
        d = [x for x in d if x > 3.0]
        if d:
            out.append(min(d))
    return out


sp["by_dynasty"] = {}
for key, dyn, reg in (("safavid_iran", "safavid", "Iran"), ("qajar_iran", "qajar", "Iran"), ("seljuk_anatolia", "seljuk", "Anatolia"),
                      ("ottoman_anatolia_roadside", "ottoman", "Anatolia")):
    rs = [r for r in inn if r["dynasty"] == dyn and r["region"] == reg and (not key.endswith("roadside") or r["setting"] == "roadside")]
    sp["by_dynasty"][key] = spacing(nn_same(rs))
saf = nn_same([r for r in inn if r["dynasty"] == "safavid" and r["region"] == "Iran"])
h, _ = np.histogram(np.clip(saf, 0, 149.99), bins=bins)
hist["safavid"] = [int(x) for x in h]

# a null model: the same number of stages scattered at random over the land of the same regions keeps much shorter gaps?
# (not used: the stages are not a random sample of the land, so no null model is claimed; only the observed gaps are reported)

# ------------------------------------------------------------------ outputs
for r in A:
    r.setdefault("stage", None)
summary = dict(
    n=len(A), n_inn=len(inn), n_ribat=sum(r["kind"] == "ribat" for r in A),
    n_urban=sum(r["setting"] == "urban" for r in A), n_roadside=sum(r["setting"] == "roadside" for r in A),
    n_stages=len(stages), n_stages_urban=sum(s["urban"] for s in stages), n_stages_rural=len(rural),
    by_region={R: dict(n=sum(1 for r in A if r["region"] == R), inns=sum(1 for r in inn if r["region"] == R),
                       roadside=sum(1 for r in A if r["region"] == R and r["setting"] == "roadside"),
                       urban=sum(1 for r in A if r["region"] == R and r["setting"] == "urban"),
                       dated=sum(1 for r in inn if r["region"] == R and r["dynasty"] != "none"),
                       listed=sum(1 for r in inn if r["region"] == R and r["listed"])) for R in REGIONS + ["Other"]},
    by_country=Counter(r["country"] for r in A).most_common(),
    by_dynasty={k: sum(1 for r in inn if r["dynasty"] == k) for k in DYN_ORDER},
    by_dynasty_region={k: dict(Counter(r["region"] for r in inn if r["dynasty"] == k).most_common()) for k in DYN_ORDER},
    dated_by=dict(Counter(r["dated_by"] for r in inn if r["dynasty"] != "none")),
    n_dated=sum(1 for r in inn if r["dynasty"] != "none"), n_with_year=sum(1 for r in inn if r["year"] is not None),
    n_style_year_conflict=sum(1 for r in inn if r["style_year_conflict"]),
    years=sorted([r["year"] for r in inn if r["year"] is not None]),
    year_errors=[dict(name=r["name"], qid=r.get("qid"), inception=r["inception"]) for r in A if r["year_how"] == "not a building date"],
    n_listed=sum(1 for r in inn if r["listed"]), n_whs=sum(1 for r in inn if r["whs"]),
    n_ruin=sum(1 for r in inn if r["ruin"]), n_reuse=sum(1 for r in inn if r["reuse"]),
    n_iran_national=sum(1 for r in inn if "Q5958900" in r.get("heritage", [])),
    sources=dict(wikidata_only=sum(1 for r in A if r["src"] == "wikidata" and not r["osm"]), both=sum(1 for r in A if r["src"] == "wikidata" and r["osm"]),
                 osm_only=sum(1 for r in A if r["src"] == "osm"), osm_only_by_name=sum(1 for r in A if r["src"] == "osm" and r.get("how") == "name")),
    spacing=sp, route_max_km=ROUTE_MAX, n_route_edges=len(route_edges), route_km=round(sum(w for _, _, w in route_edges)),
    n_mst_edges=len(edges), chains=chains[:12], n_chains=len(chains),
    stages_in_chains=int(sum(c["stages"] for c in chains)),
)
jsave(summary, f"{WORK}/analysis.json", indent=1)
jsave(stages, f"{WORK}/stages.json")

# data files
COLS = ["id", "name", "name_native", "lon", "lat", "country", "region", "setting", "dynasty", "dated_by", "year", "year_how", "inception", "inception_precision",
        "styles", "heritage", "whs", "ruin", "reuse", "stage", "qid", "osm", "enwiki", "sitelinks", "source"]
with open(f"{DATA}/caravanserais.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(COLS)
    for r in sorted(A, key=lambda r: (r["region"], r["country"], r["name"])):
        w.writerow([r["id"], dash(r["name"]), dash(r.get("name_native", "")), round(r["lon"], 6), round(r["lat"], 6), r["country"], r["region"], r["setting"],
                    DYN_LABEL[r["dynasty"]], r["dated_by"], r["year"] or "", r["year_how"] if r["year"] else "", r.get("inception") or "", r.get("inception_precision") or "",
                    "|".join(r["style_labels"]), "|".join(r["heritage_labels"]), int(r["whs"]), int(r["ruin"]), int(r["reuse"]),
                    "" if r["stage"] is None else r["stage"], r.get("qid", ""), "|".join(r["osm"]), r.get("enwiki", ""), r.get("sitelinks", ""),
                    "Wikidata and OpenStreetMap" if r["src"] == "wikidata" and r["osm"] else ("Wikidata" if r["src"] == "wikidata" else "OpenStreetMap")])
feats = []
for r in A:
    feats.append(dict(type="Feature", geometry=dict(type="Point", coordinates=[round(r["lon"], 5), round(r["lat"], 5)]),
                      properties=dict(id=r["id"], name=r["name"], native=r.get("name_native", ""), country=r["country"], region=r["region"], setting=r["setting"],
                                      dynasty=r["dynasty"], year=r["year"], year_how=r["year_how"] if r["year"] else "", styles=r["style_labels"], heritage=r["heritage_labels"],
                                      ruin=r["ruin"], reuse=r["reuse"], qid=r.get("qid", ""), osm=r["osm"][:1], enwiki=r.get("enwiki", ""),
                                      sl=r.get("sitelinks", 0), gap=stages[r["stage"]]["nn_km"] if r["stage"] is not None else None,
                                      nbr=stages[stages[r["stage"]]["nn"]]["name"] if r["stage"] is not None else "",
                                      here=stages[r["stage"]]["n"] if r["stage"] is not None else 1)))
jsave(dict(type="FeatureCollection", features=feats), f"{DATA}/caravanserais.geojson")
rf = [dict(type="Feature", geometry=dict(type="LineString", coordinates=[[round(stages[a]["lon"], 4), round(stages[a]["lat"], 4)], [round(stages[b]["lon"], 4), round(stages[b]["lat"], 4)]]),
           properties=dict(km=round(w, 1), region=stages[a]["region"])) for a, b, w in route_edges]
jsave(dict(type="FeatureCollection", features=rf), f"{DATA}/routes_inferred.geojson")
jsave(A, f"{WORK}/classified.json")
print(json.dumps({k: v for k, v in summary.items() if k not in ("years", "spacing", "by_dynasty_region")}, indent=1, ensure_ascii=False)[:5000])
print(json.dumps({k: sp[k] for k in ("all_stages", "roadside_stages", "route_edges", "by_region")}, indent=0)[:3000])
