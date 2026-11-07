"""Every number quoted anywhere (page, paper, blog, collage, Reddit post) goes into data/results.json, with checks."""
from common import *

M = jload(f"{WORK}/merge_summary.json")
A = jload(f"{WORK}/analysis.json")
C = jload(f"{WORK}/classified.json")
sp = A["spacing"]
pc = lambda a, b: round(100 * a / b, 1) if b else 0.0

inn = [r for r in C if r["kind"] == "inn"]
n, n_inn = A["n"], A["n_inn"]
tur = A["by_region"]["Anatolia"]["n"]; irn = A["by_region"]["Iran"]["n"]
bc = dict(A["by_country"])
top2 = bc["Turkey"] + bc["Iran"]
R = dict(
    meta=dict(slug=SLUG, page=PAGE, repo=REPO, doi="10.5281/zenodo.24043674", year=2026,
              title="Caravanserais of the Silk Roads", subtitle="Where the inns were, how far apart, and who built them"),
    sources=dict(wd_rows=M["wd_rows"], wd_nocoord=M["wd_nocoord"], wd_n=M["wd_n"], osm_tag_n=M["osm_tag_n"], osm_after_dupes=M["osm_after_dupes"],
                 osm_dupes=M["osm_dupes"], osm_matched=M["wd_with_osm"], osm_matched_tag=M["match"].get("osm matched by wikidata tag", 0),
                 osm_matched_dist=M["match"].get("osm matched by distance (150 m)", 0) + M["match"].get("osm matched by distance and name (500 m)", 0),
                 osm_new=A["sources"]["osm_only"], osm_new_by_name=A["sources"]["osm_only_by_name"], name_files=M["name_files"],
                 name_candidates=M["name_candidates"], wikidata_only=A["sources"]["wikidata_only"], both=A["sources"]["both"]),
    n=n, n_inn=n_inn, n_ribat=A["n_ribat"], n_urban=A["n_urban"], n_roadside=A["n_roadside"],
    pc_urban=pc(A["n_urban"], n_inn), pc_roadside=pc(A["n_roadside"], n_inn),
    n_countries=len(bc), by_country=[dict(country=k, n=v) for k, v in A["by_country"]],
    turkey=bc["Turkey"], iran=bc["Iran"], top2=top2, pc_top2=pc(top2, n),
    by_region=A["by_region"],
    stages=dict(n=A["n_stages"], urban=A["n_stages_urban"], rural=A["n_stages_rural"]),
    spacing=sp,
    routes=dict(max_km=A["route_max_km"], edges=A["n_route_edges"], km=A["route_km"], chains=A["chains"], n_chains=A["n_chains"],
                stages_in_chains=A["stages_in_chains"], pc_stages_in_chains=pc(A["stages_in_chains"], A["n_stages"])),
    dates=dict(n_dated=A["n_dated"], pc_dated=pc(A["n_dated"], n_inn), n_with_year=A["n_with_year"], pc_with_year=pc(A["n_with_year"], n_inn),
               by_style=A["dated_by"].get("style", 0) + A["dated_by"].get("style and year", 0), by_year_only=A["dated_by"].get("year", 0),
               by_dynasty=A["by_dynasty"], by_dynasty_region=A["by_dynasty_region"], conflicts=A["n_style_year_conflict"],
               years=A["years"], year_errors=A["year_errors"], first_year=A["years"][0], last_year=A["years"][-1],
               seljuk_anatolia=A["by_dynasty_region"]["seljuk"].get("Anatolia", 0),
               safavid_iran=A["by_dynasty_region"]["safavid"].get("Iran", 0), qajar_iran=A["by_dynasty_region"]["qajar"].get("Iran", 0),
               ottoman_anatolia=A["by_dynasty_region"]["ottoman"].get("Anatolia", 0),
               years_1200s=sum(1 for y in A["years"] if 1200 <= y < 1300)),
    heritage=dict(n_listed=A["n_listed"], pc_listed=pc(A["n_listed"], n_inn), n_whs=A["n_whs"], n_iran_national=A["n_iran_national"],
                  pc_iran_listed=pc(A["by_region"]["Iran"]["listed"], A["by_region"]["Iran"]["inns"]),
                  anatolia_listed=A["by_region"]["Anatolia"]["listed"], n_ruin=A["n_ruin"], n_reuse=A["n_reuse"]),
)
# derived for the text
s_all, s_saf = sp["all_stages"], sp["by_dynasty"]["safavid_iran"]
R["text"] = dict(
    nn_median=s_all["median"], nn_pc_30_40=s_all["pc_30_40"], nn_pc_under_20=s_all["pc_under_20"],
    saf_median=s_saf["median"], saf_n=s_saf["n"], saf_q1=s_saf["q1"], saf_q3=s_saf["q3"], saf_pc_20_50=s_saf["pc_20_50"], saf_pc_30_40=s_saf["pc_30_40"],
    qaj_median=sp["by_dynasty"]["qajar_iran"]["median"], route_median=sp["route_edges"]["median"],
    iran_median=sp["by_region"]["Iran"]["median"], anat_median=sp["by_region"]["Anatolia"]["median"],
    chain1=A["chains"][0], chain2=A["chains"][1],
    day_low=30, day_high=40,
)

# ---- checks: every claim the text makes in words
assert R["n"] == R["n_inn"] + R["n_ribat"]
assert R["n_urban"] + R["n_roadside"] == R["n_inn"]
assert R["sources"]["wikidata_only"] + R["sources"]["both"] + R["sources"]["osm_new"] == R["n"]
assert R["sources"]["both"] == R["sources"]["osm_matched"]
assert bc["Turkey"] > bc["Iran"] > max(v for k, v in bc.items() if k not in ("Turkey", "Iran"))   # Turkey first, Iran second
assert R["pc_top2"] > 70
assert s_all["median"] < 30, "claim: neighbours sit closer than a day's march"
assert 30 <= s_saf["median"] <= 40, "claim: one dynasty alone (Safavid) keeps a day's march"
assert s_saf["median"] > s_all["median"] + 8
assert s_saf["pc_20_50"] > 50
assert A["chains"][0]["region"] == "Anatolia" and A["chains"][1]["region"] == "Iran"
assert R["dates"]["pc_dated"] < 40 and R["dates"]["n_with_year"] < 100
d = A["by_dynasty"]
assert d["safavid"] > d["qajar"] > d["ottoman"] > d["seljuk"], "claim: Safavid most, then Qajar, Ottoman, Seljuk"
assert R["heritage"]["anatolia_listed"] <= 5, "claim: Wikidata records almost no Turkish heritage listings"
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps(R["text"], indent=1, ensure_ascii=False))
