# Your browser is the laboratory

Start with [01_observed_ocean.ipynb](01_observed_ocean.ipynb). The book displays saved outputs; **Launch browser lab** opens editable notebooks powered by Python running in your browser. They answer different needs: read the narrative here, change the experiment there.

## Run an experiment

1. Open the [Ocean Watch Lab](https://jltobias.github.io/JupyterLite-Global-Fishing-Watch-and-Dark-Vessels/lab/index.html?path=01_observed_ocean.ipynb).
2. Wait for the Python (Pyodide) kernel to become ready. A first launch may take a minute or longer on a slow connection.
3. Run the setup cell, then run the remaining cells from top to bottom with **Shift+Enter** or **Run → Run All Cells**.
4. Change a parameter such as a matching distance, radar threshold, or local seafood-retention fraction. Run its cell again and explain what changed.
5. Download your notebook using **File → Save and Export Notebook As → Notebook** before leaving.

The file browser contains `data/` and `oceanlab.py` beside the notebooks. Work is stored in browser storage and can disappear if you clear site data, use a private window, or change browsers. Export important work. Reloading a site update may retain an older notebook in your local browser storage; download your work before resetting that storage.

## Three operating modes

| Mode | What works | What it needs |
|---|---|---|
| Read the book | Saved charts, explanations, standalone interactive figures | A normal browser; JavaScript for interactive figures |
| Bundled lab | Historical data, matching, radar, health and stock experiments | First-use internet for Pyodide and packages; WebGL for 3D |
| Optional live extension | Search a satellite catalog, inspect your downloaded GFW CSV | Internet and provider CORS support; GFW account for provider downloads |

No notebook needs a secret. The GFW workbench uses **your own downloaded export** rather than embedding credentials in a public notebook. It does not issue authenticated API calls. Full-resolution SAR preprocessing belongs in a local Python or cloud geospatial environment; [the satellite chapter](05_satellite_catalog.ipynb) shows the boundary and a runnable local extraction script is supplied in the repository.

## If something does not run

**A package import fails:** run the first cell again. That cell installs browser-compatible packages in Pyodide. Corporate filtering can block package CDNs.

**A data file is missing:** keep notebooks, `oceanlab.py`, and `data/` together. Use HTTPS or localhost. JupyterLite needs its service worker to synchronize files on GitHub Pages, where cross-origin isolation headers are unavailable. Check that your browser permits service workers and site storage. [JupyterLite filesystem documentation](https://jupyterlite.readthedocs.io/en/stable/howto/content/python.html).

**A 3D plot is blank:** enable WebGL or use the accompanying 2D plot. The numerical calculations do not depend on 3D rendering. The book and browser lab include their plotting JavaScript locally; exported notebooks opened in a separate desktop Jupyter environment use the Plotly CDN. Interactive figures have titled frames and links to open them separately; data tables and explicit chart captions provide another way to inspect the result. Charts use color plus labels, marker shapes, or line styles where comparisons require them.

**A live service fails:** set `LIVE = False`. The satellite metadata snapshot and all core exercises work without live provider access. A remote error never silently substitutes invented observations.

**You want a fully offline course:** the current deployment does not package the entire Pyodide runtime. Build a dedicated offline distribution following [JupyterLite's offline guide](https://jupyterlite.readthedocs.io/en/stable/howto/configure/advanced/offline.html) and vendor package wheels. Ordinary browser caching is not an offline guarantee.
