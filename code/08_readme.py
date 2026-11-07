"""README.md and LICENSE from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); T = R["text"]; S = R["sources"]; d = R["dates"]; h = R["heritage"]
pc = lambda v: f"{round(v)}%"
readme = f"""# Caravanserais of the Silk Roads

Where the inns were, how far apart, and who built them. {R['n']:,} caravanserais, khans and ribats from Wikidata and OpenStreetMap on a hand-inked map (The Inked World), each drawn as a little walled courtyard washed in the colour of the dynasty that built it, with the inferred links between neighbouring stops and camel trains walking them.

Interactive page: https://maps.tristanhotham.com/caravanserais/
Paper: https://doi.org/{{10.5281/zenodo.24043674}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/caravanserais/}}
Code and data: https://github.com/Tristan-Hotham/caravanserais

Dr Tristan Hotham · Independent researcher · 2026

## Headline results

- **{R['n']:,} records** ({R['n_inn']:,} inns and {R['n_ribat']} ribats that are forts or Sufi lodges) in {R['n_countries']} countries and territories, merged from {S['wd_n']:,} Wikidata items and {S['osm_after_dupes']:,} OpenStreetMap features ({S['both']:,} in both).
- **Turkey ({R['turkey']:,}) and Iran ({R['iran']:,}) hold {pc(R['pc_top2'])}** of the record. Central Asia and Afghanistan have {R['by_region']['Central Asia and Afghanistan']['n']}, South Asia {R['by_region']['South Asia']['n']} and China none: a map of cataloguing as much as of history.
- **Closer than a day's march.** Grouping inns within 3 km into {R['stages']['n']:,} stops, the median gap to the nearest other stop is {T['nn_median']:.1f} km; only {pc(T['nn_pc_30_40'])} of gaps fall in the 30 to 40 km of a day's march.
- **One dynasty at a time, the day's march returns.** The {T['saf_n']} Safavid caravanserais of Iran stand a median {T['saf_median']:.1f} km from the nearest other Safavid one (quartiles {T['saf_q1']:.1f} to {T['saf_q3']:.1f} km). Later builders filled the gaps.
- **Dates are scarce.** {d['n_dated']} of {R['n_inn']:,} inns ({pc(d['pc_dated'])}) have a dynasty, nearly all from their architectural style; {d['n_with_year']} have a year. Safavid {d['by_dynasty']['safavid']}, Afsharid, Zand and Qajar {d['by_dynasty']['qajar']}, Ottoman {d['by_dynasty']['ottoman']}, Seljuk {d['by_dynasty']['seljuk']}.
- **Heritage.** {h['n_listed']} inns are listed in Wikidata ({h['n_iran_national']} Iranian National Heritage, {h['n_whs']} part of the UNESCO Persian Caravanserai); OpenStreetMap marks {h['n_ruin']} as ruins and {h['n_reuse']} as reused as hotels, guest houses, museums or restaurants.

## Files

| Path | What |
|---|---|
| `index.html`, `js/caravan.js`, `js/caravan-art.js` | The interactive page: the study's layers, filters, popups, camel trains and pen drawings |
| `../ink-map/` (sister repository) | The Inked World engine and base-map data, loaded from https://maps.tristanhotham.com/ink-map/ at run time |
| `data/caravanserais.csv`, `data/caravanserais.geojson` | One row per caravanserai: names, position, country, region, setting, dynasty, year, style, heritage, ruin or reuse, stop, Wikidata and OpenStreetMap ids |
| `data/routes_inferred.geojson` | The inferred links between neighbouring stops (minimum spanning tree, links up to {R['routes']['max_km']:.0f} km) |
| `data/results.json` | Every number quoted on the page, in the paper, the blog post and the collage |
| `code/` | Numbered scripts from the raw files to everything (below) |
| `img/` | Figures for the page |
| `release/paper/` | The paper (PDF and LaTeX) |
| `release/blog/` | Blog post (WordPress block markup), its figures and meta |
| `release/zenodo/` | Files and metadata for the Zenodo record |
| `reddit/` | The collage, its script and the post |
| `header.png` | Social card |

## Method

1. `01_merge.py`: Wikidata items that are caravanserais (Q186347), khans (Q115921107) or ribats (Q1333989), or subclasses, with coordinates; OpenStreetMap features tagged historic, building, heritage:type or amenity = caravanserai. OpenStreetMap duplicates within 60 m merged; OpenStreetMap features matched to Wikidata by their wikidata tag or within 150 m. A wider OpenStreetMap name search (khan, han, ribat and so on) was planned, and the script will use its files if they are present, but they were not available for this version.
2. `02_analyse.py`: countries from Natural Earth; seven ribats in Tunisia, Portugal and Spain flagged as forts or lodges; urban or roadside (within 2 to 5 km of a Natural Earth town of 50,000 or more by size, or in a cluster of inns); stops (inns within 3 km); nearest-neighbour gaps, overall and within each dynasty; links (minimum spanning tree over each stop's ten nearest neighbours, cut at {R['routes']['max_km']:.0f} km); dynasty from the Wikidata architectural style or from the year and region.
3. `03_results.py`: `data/results.json`, with asserts on every claim made in words.
4. `04_figures.py`: charts. `qa_shot.js`: Playwright renders of the page for QA and the map figures.
5. `05_build_page.py`, `06_paper.py`, `07_release.py`, `08_readme.py`: page, paper, blog and Zenodo, README. `reddit/collage.py` and `code/09_header.py`: collage and social card.

## Caveats

This is a map of records, not of history: Turkey and Iran dominate because they are well catalogued. Most inns are undated, a style can reflect a restoration, the urban rule is a rule of thumb, distances are straight lines, and the links and camel trains illustrate the inferred network rather than mapped roads.

## Sources and licences

- Wikidata (CC0).
- © OpenStreetMap contributors, ODbL 1.0, via the Overpass API. The data files in `data/` contain OpenStreetMap-derived data and are available under the ODbL 1.0.
- Natural Earth 1:10m countries and populated places (public domain).
- Base map: The Inked World (Hotham 2026, https://doi.org/10.5281/zenodo.23860253), drawn live from OpenStreetMap via OpenFreeMap, AWS Terrain Tiles, RESOLVE Ecoregions 2017 (CC BY 4.0) and Natural Earth.
- MapLibre GL JS 4.7.1 (BSD 3-Clause).

## How to rerun

```
cd code
python3 01_merge.py && python3 02_analyse.py && python3 03_results.py && python3 04_figures.py
python3 05_build_page.py
# serve the folder that holds both caravanserais/ and ink-map/, then render the map figures, e.g.
#   node qa_shot.js shots.json      (needs Playwright and a local maplibre-gl 4.7.1)
python3 06_paper.py && python3 07_release.py && python3 08_readme.py && python3 09_header.py && python3 ../reddit/collage.py
```

Raw inputs are listed in `code/common.py`.

## Citation

Hotham, T. (2026) Caravanserais of the Silk Roads: where the inns were, how far apart, and who built them. Zenodo. https://doi.org/{{10.5281/zenodo.24043674}}

## Licence

Code: MIT. Text and figures: CC BY 4.0. Data: ODbL 1.0 (contains OpenStreetMap data; Wikidata content is CC0). See `LICENSE`.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in readme.replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License (code: code/, js/, index.html)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures, the paper, the collage and the header image: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/

Data (data/ and release/zenodo/ data files): Open Database License 1.0 (ODbL), https://opendatacommons.org/licenses/odbl/1-0/ , because they contain data from OpenStreetMap (© OpenStreetMap contributors). The Wikidata content they contain is CC0.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README", len(readme))
