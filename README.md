# Caravanserais of the Silk Roads

Where the inns were, how far apart, and who built them. 960 caravanserais, khans and ribats from Wikidata and OpenStreetMap on a hand-inked map (The Inked World), each drawn as a little walled courtyard washed in the colour of the dynasty that built it, with the inferred links between neighbouring stops and camel trains walking them.

Interactive page: https://maps.tristanhotham.com/caravanserais/
Paper: https://doi.org/10.5281/zenodo.24043674
Blog post: https://blog.tristanhotham.com/2026/10/31/caravanserais/
Code and data: https://github.com/Tristan-Hotham/caravanserais

Dr Tristan Hotham · Independent researcher · 2026

## Headline results

- **960 records** (953 inns and 7 ribats that are forts or Sufi lodges) in 33 countries and territories, merged from 864 Wikidata items and 281 OpenStreetMap features (185 in both).
- **Turkey (401) and Iran (352) hold 78%** of the record. Central Asia and Afghanistan have 52, South Asia 17 and China none: a map of cataloguing as much as of history.
- **Closer than a day's march.** Grouping inns within 3 km into 727 stops, the median gap to the nearest other stop is 20.9 km; only 12% of gaps fall in the 30 to 40 km of a day's march.
- **One dynasty at a time, the day's march returns.** The 90 Safavid caravanserais of Iran stand a median 33.7 km from the nearest other Safavid one (quartiles 25.7 to 50.1 km). Later builders filled the gaps.
- **Dates are scarce.** 311 of 953 inns (33%) have a dynasty, nearly all from their architectural style; 61 have a year. Safavid 97, Afsharid, Zand and Qajar 78, Ottoman 70, Seljuk 29.
- **Heritage.** 311 inns are listed in Wikidata (213 Iranian National Heritage, 47 part of the UNESCO Persian Caravanserai); OpenStreetMap marks 36 as ruins and 17 as reused as hotels, guest houses, museums or restaurants.

## Files

| Path | What |
|---|---|
| `index.html`, `js/caravan.js`, `js/caravan-art.js` | The interactive page: the study's layers, filters, popups, camel trains and pen drawings |
| `../ink-map/` (sister repository) | The Inked World engine and base-map data, loaded from https://maps.tristanhotham.com/ink-map/ at run time |
| `data/caravanserais.csv`, `data/caravanserais.geojson` | One row per caravanserai: names, position, country, region, setting, dynasty, year, style, heritage, ruin or reuse, stop, Wikidata and OpenStreetMap ids |
| `data/routes_inferred.geojson` | The inferred links between neighbouring stops (minimum spanning tree, links up to 80 km) |
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
2. `02_analyse.py`: countries from Natural Earth; seven ribats in Tunisia, Portugal and Spain flagged as forts or lodges; urban or roadside (within 2 to 5 km of a Natural Earth town of 50,000 or more by size, or in a cluster of inns); stops (inns within 3 km); nearest-neighbour gaps, overall and within each dynasty; links (minimum spanning tree over each stop's ten nearest neighbours, cut at 80 km); dynasty from the Wikidata architectural style or from the year and region.
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

Hotham, T. (2026) Caravanserais of the Silk Roads: where the inns were, how far apart, and who built them. Zenodo. https://doi.org/10.5281/zenodo.24043674

## Licence

Code: MIT. Text and figures: CC BY 4.0. Data: ODbL 1.0 (contains OpenStreetMap data; Wikidata content is CC0). See `LICENSE`.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
