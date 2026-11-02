# Methods, provenance, and reproducibility

## The observed data pipeline

`scripts/fetch_public_data.py` downloads selected files from the [Paolo et al. analysis-data deposit](https://doi.org/10.6084/m9.figshare.24309475). It verifies the provider's MD5 checksum before saving each file and records SHA-256 checksums, immutable file IDs, the article version, retrieval date, and license in `data/download_manifest.json`.

`scripts/prepare_data.py` derives two browser-friendly products from `raster_5th_degree.feather`:

- `sar_activity_2017_2021.npz`: selected original columns and cell-center coordinates. Latitude and longitude equal the source index divided by five, plus 0.1°. Missing values remain missing.
- `sar_activity_1deg.csv`: sums of source-cell per-overpass normalized activity grouped into 1° bins, using `min_count=1`. This is a map proxy, not a count of unique vessels. It is not corrected for the unequal physical area of longitude–latitude cells.

The source README is retained verbatim. It contains a typo in the stated `AIS_nonfishing` formula and some continent-table columns have names that do not match intuitive fraction definitions. We use the supplied named component values and recompute fishing shares explicitly from `dark_fishing / tot_fishing` or `unmatched_fishing / (matched_fishing + matched_unknown_likelyfish + unmatched_fishing)`. We do not use the precomputed `perc_dark_*` or `dark_fishing_frac` fields. Notebooks show the denominator.

Fractional values reflect model probabilities and normalization. They are expected activity, not fractional physical ships. Five source rows have missing fishing-related values; notebook 01 reports missingness, and derived map bins preserve all-missing groups. The snapshot covers a historical study domain with uneven imagery coverage. It is not current fleet intelligence.

## Satellite metadata versus pixels

The Sentinel-1 STAC snapshot contains three scene records and asset references for a fixed southern Baltic search in June 2024. It contains **metadata only**. A separate bundled 512 × 512 VV crop near Rostock contains actual calibrated gamma0 intensity pixels from the second catalog item. Its provenance includes the acquisition time, CRS, transform, unsigned asset URL and checksum. No vessel labels or AIS matches are supplied for that crop. The synthetic radar scene contains **no real satellite pixels**. The optional local script can extract additional windows from signed Planetary Computer assets and saves a separate provenance file. Never label a synthetic scene as Sentinel-1, ICEYE, or an observed vessel detection.

## Teaching models

An additional bounded environmental input contains available NOAA NCEI OISST v2.1 final daily analysis values and provider error estimates for one Baltic grid cell in 2024. The raw CSV retains the units row; the normalized CSV removes that row without imputing values. Temporal archive gaps, the exact ERDDAP query, terms and checksums are retained. Notebook 06 reindexes dates for plotting so missing dates break the line; it displays this observed analysis product separately, and its later seasonal/effort simulation is generated independently. OISST is a merged and interpolated analysis, and its provider error SD is not a complete uncertainty estimate for a local health study.

| Model | Deliberate simplification | Suitable use |
|---|---|---|
| AIS–SAR assignment | Distance/time score; no motion estimation or SAR displacement correction | Explore sensitivity and one-to-one matching |
| Radar detector | Exponential speckle, Gaussian targets, masked local reference ring | Understand contrast, false alarms and missed targets |
| Environmental series | Shared seasonal cycle and trend; no measured disease | Explore confounding |
| Food accounting | Fixed edible fraction and protein fraction | Explore distribution and dimensional analysis |
| Stock model | Logistic growth, constant fishing mortality, single stock | Explore feedback, thresholds and recovery |

Seeds are fixed in the code. The stock model uses explicit Euler steps of 0.05 years and clamps biomass at zero. It omits recruitment variability, age structure, food-web interactions, spatial movement and adaptive management. None of its parameters are fitted to a real stock.

## Build and verification

The repository uses a pinned Jupyter Book 1/Sphinx stack, with notebook execution controlled by `scripts/execute_notebooks.py`. Book 1 is in maintenance mode; migrating to Book 2 should include new build and visual checks. The deployment combines the book at the site root with JupyterLite at `/lab/`. A GitHub Actions workflow executes notebooks, validates provenance and content, builds both sites, and deploys a Pages artifact.

Core checks require no provider login and do not refresh external data. Refreshing public inputs is an explicit operation, so a remote data change cannot silently alter an ordinary build. Package pins describe the local build environment; Pyodide supplies its own compatible numerical package builds in the browser. Record those versions when exporting a browser experiment.

## Interpret responsibly

Preserve uncertainty and data rights when sharing results. Consider safety and privacy before publishing detailed locations or identities of vulnerable fishers. Partner with affected communities when collecting or interpreting health and livelihood data. A public educational map is not a compliance determination or an individual health assessment.
