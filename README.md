# Lintu FireAtlas: Fire Activity Calendar (Türkiye + USA)

**Team Lintu · NASA Space Apps Challenge 2026**
**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

26 years of NASA FIRMS fire detections from two satellites (MODIS 2000–2026, VIIRS 2012–2026), merged into one consistent calendar and map of fire activity in Türkiye.

- **Live app:** https://lintuteam.github.io/lintu-fireatlas/ (works on phones too)
- **USA view:** https://lintuteam.github.io/lintu-fireatlas/arayuz/abd.html (or the **ABD** button in the app header)
- **Demo (7 slides):** [demo/Lintu_Demo_7_Slides.pdf](demo/Lintu_Demo_7_Slides.pdf)

> This is a record of **past fire activity**, not a fire-risk forecast. A satellite hot spot is not always a fire.

## The problem

MODIS (since 2000, 1 km pixels) retires in 2027. VIIRS (since 2012, 375 m pixels) also sees small fires. When VIIRS joined in 2012, raw fire counts over Türkiye jumped by **+143%**, while MODIS alone fell by **−45%** over the same period (2009–11 vs 2012–14). The jump comes from the new sensor, not from more fires.

## Our solution

| Step | What we do | Result |
|---|---|---|
| 1. Raw data | NASA FIRMS MODIS C6.1 + VIIRS 375 m over Türkiye | 1,414,674 detections |
| 2. Cleaning | Each detection gets one label (clean fire, stubble burning, static/industrial heat, offshore, volcano…). Nothing is deleted | 1,044,222 clean + stubble detections |
| 3. Clustering | Detections close in space and time, from both satellites together, are linked; each connected group is one fire event | 471,978 events; 59,201 double counts avoided; 2012 jump +143% → +31% |
| 4. Harmonization | VIIRS is divided by the number of satellites flying, then scaled by a region × season × fire-power ratio into a MODIS-equivalent series | Leave-one-year-out (2012–2025): yearly MAPE 8.3%, R² 0.87 |

## Validation

- The final activity map highlights the same regions as the Türkiye wildfire risk map published by TRT Haber.
- With no official data in the model, our largest event is the **2021 Manavgat fire** (6,740 detections, ~218 hours), matching the official dates of 28 July – 6 August 2021.
- Of our 20 largest events, 16 match documented wildfires, 3 match partly and 1 was not found. Sources are listed in [belgeler_ve_denetim/gercek_dogrulama.md](belgeler_ve_denetim/gercek_dogrulama.md).

## Second country: USA (2009–2015)

To check that the method is not tuned to Türkiye, we ran the same pipeline on the NASA FIRMS archive for the USA (2.72 million detections, 2009–2015).

| Measure | Türkiye (2000–2026) | USA (2009–2015) |
|---|---|---|
| Raw 2012 jump (2009–11 → 2012–14) | +143.1% | +318.6% |
| Real MODIS, same period | −44.9% | −2.1% |
| Our MODIS-equivalent series | −41.4% | −4.8% |
| Gap to real MODIS | 3.5 points | 2.7 points |
| Yearly leave-one-year-out error (MAPE) | 8.3% | 4.2% |
| Documented fires matched | 16 of the 20 largest events | 32 of 33 |

An independent re-computation, written separately from the pipeline code, reproduced the counts, jumps and LOYO errors exactly. Full report (Turkish): [raporlar/ABD_DOGRULAMA_RAPORU.md](raporlar/ABD_DOGRULAMA_RAPORU.md). Pipeline: `kaynak_kod/abd/abd_hat.py` (needs the FIRMS USA archive converted with `veri_abd/xlsx_to_parquet.py`; the raw file is not included).

## Features

- **Calendar:** years × months, coloured by fire events. ★ marks each year's busiest month and 🔥 the month of that year's biggest fire. Click a month to open its fires on the map.
- **Map:** a heat map when zoomed out and single events up close. Province, circle and polygon selection, a stubble-burning filter, the top 10 fires by power (FRP), and a "2012 jump mode" (raw → clustered → corrected).
- **Accessibility:** colour-blind-safe palettes (Viridis/Cividis) and a one-click protan/deutan/tritan simulation.
- **Lintu:** a 14-step guided tour. Turkish and English.
- **Offline:** no external CDN; all libraries are bundled.
- **Mobile:** single-column layout on phones; the filter panel folds into a "Süzgeçler / Filters" button.
- **Türkiye | ABD switch:** the USA validation view (`arayuz/abd.html`) with its own map, calendar and documented-fire table.

## Run it locally

The app is a static web page; it needs a local web server because it loads data files.

```bash
cd arayuz
python -m http.server 8765
```

Then open http://localhost:8765. On Windows you can also double-click `BASLAT_ARAYUZ.bat`.

## Repository layout

| Folder | Content |
|---|---|
| `arayuz/` | The web app (HTML/CSS/JS, Leaflet, pre-built data in `data/`, USA data in `data_abd/`) |
| `veri_abd/` | USA inputs and outputs: documented fires, metrics, independent check |
| `kaynak_kod/` | Data pipeline (Python): cleaning, clustering, harmonization, acceptance tests. How to rerun: `kaynak_kod/NASIL_CALISTIRILIR.md` |
| `belgeler_ve_denetim/` | Method documents, audit log, validation results |
| `raporlar/` | Reports (working principle, maths and physics) |
| `demo/` | 7-slide demo deck (PDF and PPTX) |

Raw FIRMS files (~127 MB) are not included. Download them from https://firms.modaps.eosdis.nasa.gov/download/ (MODIS C6.1 and VIIRS 375 m for Türkiye). Some documents in the folders above are in Turkish.

## Data and credits

- **NASA FIRMS:** MODIS Collection 6.1 (Terra, Aqua) and VIIRS 375 m (Suomi NPP, NOAA-20, NOAA-21) active fire detections, 2000-11-01 to 2026-11-12.
- **OpenStreetMap contributors** (ODbL), via the Overpass API, for industrial-site flags.
- **Province boundaries:** cihadturhan/tr-geojson.
- **USA documented fires:** InciWeb, NIFC, USFS and Wikipedia (list in `veri_abd/belgelenmis_yanginlar_abd.json`).
- **Leaflet** (BSD-2-Clause).

## Use of AI

AI assistants were used to help write and debug code, draft documentation and prepare the demo deck. The Lintu logo and the Lintu mascot are AI-generated images.

## Team Lintu

| Name | Role |
|---|---|
| Yusuf Emir Doğan | Team captain |
| Tolga Küçüktürkmen | AI & NLP |
| Tunahan Karataş | Interface & data |
| Alperen Aydın Köysüren | UI/UX design |
| Cemal Özdemir | Product & partnerships |

Website: https://lintuteam.com
