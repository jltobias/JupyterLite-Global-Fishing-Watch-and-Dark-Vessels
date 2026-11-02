# Ocean Watch Lab

Open `01_observed_ocean.ipynb`, select Python (Pyodide), and run all cells.
The first cell downloads the numerical packages. Keep `oceanlab.py` and `data/`
beside the notebooks. Export notebooks to save your work outside browser storage.

The book: https://jltobias.github.io/JupyterLite-Global-Fishing-Watch-and-Dark-Vessels/

Bundled observations: Paolo et al. (2024), 2017–2021 SAR analysis, CC BY 4.0.
https://doi.org/10.6084/m9.figshare.24309475

Real radar crop: contains modified Copernicus Sentinel data (2024), processed
by Microsoft Planetary Computer. See its provenance JSON for the exact scene.
Coastline: Natural Earth v5.1.2, public domain.

All synthetic positions, radar experiments, food and stock scenarios are labeled.
Unmatched detections do not prove illegal fishing. Activity does not measure
catch, stock biomass or disease. Current GFW platform exports have separate terms.

The notebooks do not require an API token. Optional satellite discovery is off
by default; the GFW export workbench uses a synthetic schema example until you
explicitly supply your own CSV and its source record.
