"""Author the teaching notebooks from readable cell sources (no execution)."""
from pathlib import Path
from textwrap import dedent
import argparse
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SELECTED=set()
SETUP = '''
import sys
if sys.platform == "emscripten":
    import micropip
    await micropip.install(["numpy", "pandas", "matplotlib", "scipy", "plotly"])
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import oceanlab as lab
from IPython.display import display
print("Runtime:", sys.version.split()[0], "| NumPy:", np.__version__, "| pandas:", pd.__version__)
'''


def md(text):
    return nbf.v4.new_markdown_cell(dedent(text).strip())


def code(text):
    return nbf.v4.new_code_cell(dedent(text).strip())


def notebook(name, title, intro, cells):
    if SELECTED and name not in SELECTED:return
    launch = f"https://jltobias.github.io/JupyterLite-Global-Fishing-Watch-and-Dark-Vessels/lab/index.html?path={name}.ipynb"
    nb = nbf.v4.new_notebook(cells=[md(f"# {title}\n\n[Run this notebook in your browser ↗]({launch})\n\n{dedent(intro).strip()}"), md("Run the setup cell first. Browser Python downloads numerical packages on first use. Core exercises use bundled files; live access is optional. Export your notebook to preserve work."), code(SETUP)] + cells)
    nb.metadata.update({"kernelspec": {"display_name": "Python (Pyodide)", "language": "python", "name": "python"},
                        "language_info": {"name": "python"}, "oceanwatch": {"data_date": "2026-11-01", "version": "1.0.0"}})
    nbf.write(nb, CONTENT / (name + ".ipynb"))


def main():
    global SELECTED
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only",nargs="+",default=[],help="Regenerate named notebooks without touching the others")
    SELECTED=set(parser.parse_args().only)
    notebook("01_observed_ocean", "01 · The observed ocean", '''
    **Evidence: published observations with modeled classifications.** Explore 139,189 source cells from the 2017–2021 Sentinel-1 study. Learn to distinguish normalized activity, an unmatched fraction, and image coverage.

    **Sources:** [Paolo et al. (2024)](https://doi.org/10.1038/s41586-023-06825-8), [analysis data](https://doi.org/10.6084/m9.figshare.24309475) (CC BY 4.0); Natural Earth coastline (public domain). These are historical study products, not live AIS or satellite detections.
    ''', [
        md("## Read the evidence ledger\nThe compressed table preserves selected source values and missingness. Coordinates are cell centers: original index / 5 + 0.1°. Fractional values reflect normalized and model-weighted activity, not fractions of physical ships."),
        code('''
        observed = lab.activity(full=True)
        display(observed.head())
        display(pd.DataFrame({"missing_cells": observed.isna().sum()}))
        print(f"{len(observed):,} source cells; coverage: 2017–2021")
        '''),
        md("## Map the activity\nThe default world map groups 0.2° source cells into 1° bins and sums normalized activity. This proxy is **not fishing hours, catch, or unique vessels**. Longitude–latitude bins have unequal physical areas. Empty areas are not zero activity. Change `REGION` to `(-20, 0, 0, 25)` for West Africa or `(-12, 48, 32, 66)` for Northern Europe."),
        code('''
        REGION = (-180, -60, 180, 80)  # west, south, east, north in degrees
        fig = lab.map2d("tot_fishing", bbox=REGION)
        plt.show()
        '''),
        code('''
        lab.show(lab.interactive_map())
        '''),
        md("## The denominator changes the story\nCompute the unmatched modeled fishing share yourself. Do not use the continent table's precomputed `perc_dark_*` or `dark_fishing_frac` columns. A minimum-activity screen prevents tiny denominators from dominating this descriptive comparison; it does not establish statistical significance."),
        code('''
        MIN_ACTIVITY = 1.0
        region = observed[observed.lon.between(-12,32) & observed.lat.between(48,66)].copy()
        region["unmatched_share"] = region.dark_fishing / region.tot_fishing.where(region.tot_fishing > 0)
        enough = region[region.tot_fishing >= MIN_ACTIVITY]
        display(enough[["lon", "lat", "tot_fishing", "dark_fishing", "unmatched_share", "overpasses_2017_2021"]].sort_values("tot_fishing", ascending=False).head(12))
        print("Cells retained:", len(enough), "of", len(region), "in the teaching window")
        fig, ax = plt.subplots()
        p = ax.scatter(enough.overpasses_2017_2021, enough.unmatched_share,
                       c=np.log10(enough.tot_fishing), cmap="viridis", s=12, alpha=.6)
        ax.set(xlabel="Source imagery overpasses, 2017–2021", ylabel="Unmatched modeled fishing share", ylim=(0,1),
               title="OBSERVED STUDY PRODUCT | share, coverage and denominator")
        fig.colorbar(p, ax=ax, label="log10 normalized fishing activity")
        plt.show()
        '''),
        md("## Compare components across study regions\nThe continent figures use the deposit's aggregate estimates. They do not enumerate unique vessels, indicate violations, or describe all fleets. Compare the matched and unmatched **components**, not the source's ambiguously named fraction fields."),
        code('''
        continents = pd.read_csv(lab.DATA / "vessels_bycontinent_v20230803.csv")
        cols = ["continent", "AIS fishing", "dark fishing"]
        display(continents[cols].round(2))
        ax = continents.set_index("continent")[["AIS fishing", "dark fishing"]].plot.barh(stacked=True, color=[lab.TEAL, lab.AMBER])
        ax.set(xlabel="Study's aggregate normalized fishing activity", title="OBSERVED STUDY PRODUCT | public tracking misses part of the picture")
        ax.legend(["AIS-matched component", "Unmatched component"])
        plt.tight_layout(); plt.show()
        '''),
        md("## Interpret before exporting\n1. Which claims depend on the sampling design?\n2. How would equal-area bins change a density comparison?\n3. Would an unmatched fraction identify intentional concealment?\n4. What additional data would connect this activity to a fish stock?\n\n**Takeaway:** observations make activity visible; denominators and coverage determine which comparisons are defensible.")
    ])
    notebook("02_ocean_in_3d", "02 · Think in three dimensions", '''
    **Evidence: observed study data on the globe; a separate synthetic ocean scene.** Use the globe to inspect spatial relationships without a map seam, then use a cutaway to reason about what a sensor can and cannot observe.

    [Study data](https://doi.org/10.6084/m9.figshare.24309475), CC BY 4.0; coastline: Natural Earth, public domain. No external basemap or map-service token is required. WebGL is needed for the 3D views.
    ''', [
        md("## Rotate the observed ocean\nDrag to rotate, scroll to zoom, and hover for cell values. Color is log10 of the summed normalized activity proxy in 1° bins. All points have a small illustrative altitude to avoid overlap with the sphere; altitude is **not** a data variable."),
        code("lab.show(lab.globe())"),
        md("## Check the geometry\nThe conversion from longitude and latitude to a unit sphere is explicit. At 0° longitude, 0° latitude, the point is (1,0,0). The Earth is approximated as a sphere for visualization. This does not calculate precise navigational distances."),
        code('''
        example = pd.DataFrame({"lon": [0,90,0], "lat": [0,0,90]})
        x,y,z = lab.sphere(example.lon.to_numpy(), example.lat.to_numpy())
        display(example.assign(x=x, y=y, z=z).round(6))
        '''),
        md("## From orbit to ecosystem\nThis **synthetic** scene separates the surface vessel observation from the ecosystem below. SAR does not see fish stocks or the seabed through seawater. The bathymetry, satellite height, beam positions and vessels are illustrative, with no geographic claim."),
        code("lab.show(lab.ocean_scene())"),
        md("## A 2D companion\nA globe hides the far side and can make precise value comparisons difficult. Keep a flat map and a data table beside it. The 3D view is a reasoning aid, not an automatic improvement in analytical accuracy."),
        code("lab.map2d(bbox=(-20,40,35,70)); plt.show()"),
        md("**Try it:** choose a pattern that is clearer on the globe and one that is clearer in 2D. Identify every vertical dimension in the scene that could be mistaken for a measured quantity. Write captions that prevent that mistake.")
    ])
    notebook("03_matching_and_uncertainty", "03 · When is a detection unmatched?", '''
    **Evidence: synthetic positions and invented identifiers.** Explore how a matching rule creates an unmatched category. None of the positions identify real vessels.

    Context: [GFW SAR product definitions](https://api-doc.globalfishingwatch.org/our-apis/documentation/docs/v3/4wings/). This transparent teaching algorithm is not GFW's matching algorithm.
    ''', [
        md("## A crowded patch of sea\nWe invent ten AIS candidate positions and ten SAR detections. Positions are assumed to have been projected to acquisition time. `minute` represents the time offset of supporting evidence. Real analysis must propagate vessel motion and location uncertainty, including SAR displacement effects."),
        code('''
        sar, ais = lab.matching_demo()
        MAX_KM, MAX_MINUTES = 3.0, 15.0
        matched = lab.match_points(sar, ais, max_km=MAX_KM, max_minutes=MAX_MINUTES)
        display(matched)
        fig, ax = plt.subplots()
        ax.scatter(ais.lon, ais.lat, marker="^", c="#087e83", label="Synthetic AIS candidates")
        ax.scatter(sar.lon, sar.lat, marker="o", facecolors="none", edgecolors="#bd6e13", s=65, label="Synthetic SAR detections")
        for row in matched.dropna(subset=["match"]).itertuples():
            a = ais[ais.id == row.match].iloc[0]
            ax.plot([row.lon,a.lon], [row.lat,a.lat], color="gray", lw=.8)
        ax.set(xlabel="Longitude (°)", ylabel="Latitude (°)", title="SYNTHETIC MATCHING | one identity per detection")
        ax.legend(); plt.show()
        '''),
        md("## Sensitivity is part of the result\nThe algorithm enforces one-to-one matches and allows an unmatched choice. It maximizes valid matches and then minimizes normalized distance-plus-time cost. It has no truth labels for the three added detections: a plausible correspondence is not a verified identity."),
        code('''
        rows=[]
        for km in [.25,.5,1,2,3,5,10]:
            result=lab.match_points(sar,ais,max_km=km,max_minutes=MAX_MINUTES)
            rows.append({"distance_gate_km":km,"matched":result.match.notna().sum(),"unmatched":result.match.isna().sum()})
        sensitivity=pd.DataFrame(rows)
        display(sensitivity)
        ax=sensitivity.plot(x="distance_gate_km",y=["matched","unmatched"],marker="o",color=["#087e83","#bd6e13"])
        ax.set(ylabel="Synthetic detection count",title="SYNTHETIC SENSITIVITY | the rule changes the category")
        plt.show()
        '''),
        md("## A defensible interpretation\nChange the time gate while holding distance fixed. What happens when you require evidence within one minute? Could an apparently unmatched detection become matched with better reception? Explain why a larger gate can reduce unmatched counts while increasing false identity assignments.\n\n**Do not conclude:** the unmatched count is a count of illegal vessels. **Report instead:** the number of candidates without a valid counterpart under the stated rule and evidence coverage.")
    ])
    notebook("04_sar_detection", "04 · A radar return is not a vessel label", '''
    **Evidence: a real calibrated Sentinel-1 crop, followed by a separately labeled synthetic detection experiment.** The real crop has no validated vessel annotations. The simulation supplies known target positions so we can evaluate detector behavior.

    Sources: Copernicus Sentinel data (2024), processed through Microsoft Planetary Computer; [Sentinel-1 processing background](https://developers.google.com/earth-engine/guides/sentinel1). See `data/sentinel1_real_window.provenance.json` for the scene, acquisition, coordinate reference system and exact transformation.
    ''', [
        md("## Inspect actual radar pixels\nThe crop is a 512 × 512 window near Rostock harbor. The physical quantity is terrain-corrected **gamma0 linear intensity**. Convert positive values with `10 log10(I)` for display. This is not the sigma0 Earth Engine collection; different processing products should not be treated as interchangeable. The broad color stretch is illustrative. Bright returns can be buildings, infrastructure, vessels, or other structures."),
        code('''
        provenance=json.loads((lab.DATA/"sentinel1_real_window.provenance.json").read_text())
        with np.load(lab.DATA/"sentinel1_real_window.npz") as archive:
            real=archive["gamma0_linear"]
        real_db=10*np.log10(np.where(real>0,real,np.nan))
        display(pd.Series({k:provenance[k] for k in ["item_id","acquired","band","units","center_lon_lat","shape"]}))
        fig,ax=plt.subplots()
        p=ax.imshow(real_db,cmap="gray",vmin=-25,vmax=5)
        ax.set(xlabel="Source pixel column",ylabel="Source pixel row",title="OBSERVED SENTINEL-1 | Rostock coastal window, June 2024")
        fig.colorbar(p,ax=ax,label="Gamma0 backscatter (dB)")
        plt.show()
        print(provenance["attribution"])
        '''),
        md("## Build an experiment with known targets\nThe remaining cells use **synthetic pixels**. Exponential speckle approximates a simple single-look intensity model; actual multilooked RTC statistics are more complex. Four bright targets are injected into a variable ocean background. A land mask excludes shoreline returns. Thresholding operates in linear intensity, not dB."),
        code('''
        ALPHA=7.0
        image,land,truth=lab.radar()
        candidates,background=lab.radar_detect(image,land,alpha=ALPHA)
        display(pd.Series(lab.detection_metrics(candidates,truth)))
        lab.radar_plot(ALPHA); plt.show()
        '''),
        md("## See the return in 3D\nHeight is backscatter in decibels, **not ship height**. Drag to inspect the injected target and surrounding speckle."),
        code("lab.show(lab.radar_surface())"),
        md("## Precision, recall and the price of a threshold\nCandidates are local maxima. We match them one-to-one to injected target centers within three pixels. A duplicate candidate cannot count as a second true positive. These scores describe this toy image only; they do not estimate real-world ship detection performance."),
        code('''
        rows=[]
        for alpha in [3,4,5,6,7,8,10,14,20,40,60,80]:
            points,_=lab.radar_detect(image,land,alpha=alpha)
            rows.append({"alpha":alpha,**lab.detection_metrics(points,truth)})
        scores=pd.DataFrame(rows)
        display(scores)
        ax=scores.plot(x="alpha",y=["precision","recall"],marker="o",color=["#087e83","#bd6e13"])
        ax.set(ylim=(-.05,1.05),ylabel="Object-level score",title="SYNTHETIC DETECTOR | threshold trade-off")
        plt.show()
        '''),
        md("## What would make a real detector credible?\nWe would need a trustworthy land/infrastructure mask, sensor-specific calibration, labeled independent scenes, vessel-size and sea-state strata, coverage accounting, and validation of both false alarms and missed vessels. The toy detector is not applied to the real crop as a validated ship classifier. Inspect the actual crop and explain why a simple brightness rule would confuse the harbor with vessels.\n\n**Extension:** `scripts/fetch_sar_window.py` extracts another small calibrated window locally. It uses range reads, never loads a full gigabyte-scale scene, and records provenance. New extractions change the evidence; retain the original file and its citation when comparing.")
    ])
    notebook("05_satellite_catalog", "05 · Find the satellite evidence", '''
    **Evidence: real STAC metadata, with optional live discovery.** Learn to find acquisitions, inspect sensor properties, and separate a catalog record from actual pixel analysis. The core exercise uses three bundled Sentinel-1 metadata records for June 2024 near the southern Baltic.

    Sources: [Microsoft Planetary Computer STAC documentation](https://planetarycomputer.microsoft.com/docs/quickstarts/reading-stac/) and [Sentinel-1 RTC catalog](https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc). Metadata is not an ICEYE product.
    ''', [
        code('''
        snapshot=json.loads((lab.DATA/"sentinel1_stac_snapshot.json").read_text())
        def scene_table(collection):
            rows=[]
            for item in collection.get("features",[]):
                p=item["properties"]
                rows.append({"id":item["id"],"time_utc":p.get("datetime"),"orbit":p.get("sat:orbit_state"),
                    "polarizations":str(p.get("sar:polarizations")),"mode":p.get("sar:instrument_mode"),
                    "assets":", ".join(item["assets"])})
            return pd.DataFrame(rows)
        display(scene_table(snapshot))
        first=snapshot["features"][0]
        display(pd.Series(first["assets"]["vv"]))
        '''),
        md("## Optional: repeat the discovery query\nLeave `LIVE = False` to reproduce the saved exercise. Enable it to query the public catalog without credentials. The request is limited to three records. Browser cross-origin restrictions, provider outages, or throttling can prevent live access; the message below identifies a failed query and keeps the saved snapshot explicitly labeled."),
        code('''
        LIVE=False
        query={"collections":["sentinel-1-rtc"],"bbox":[11.5,54.0,13.5,55.0],
               "datetime":"2024-06-01T00:00:00Z/2024-06-30T23:59:59Z","limit":3}
        endpoint="https://planetarycomputer.microsoft.com/api/stac/v1/search"
        if LIVE:
            try:
                if sys.platform=="emscripten":
                    from pyodide.http import pyfetch
                    response=await pyfetch(endpoint,method="POST",headers={"Content-Type":"application/json"},body=json.dumps(query))
                    if not response.ok: raise RuntimeError(f"HTTP {response.status}")
                    live=await response.json()
                else:
                    import urllib.request
                    request=urllib.request.Request(endpoint,data=json.dumps(query).encode(),headers={"Content-Type":"application/json"})
                    with urllib.request.urlopen(request,timeout=30) as response: live=json.load(response)
                print("LIVE RESPONSE; empty results mean no records returned, not no vessels.")
                display(scene_table(live))
            except Exception as error:
                print("Live discovery failed:",type(error).__name__,"— use the labeled saved snapshot above.")
        else:
            print("SAVED SNAPSHOT MODE — live network request disabled")
        '''),
        md("## Design a multisensor comparison\nDo not add unlike sensors as if their detections were independent counts of unique boats. Match acquisition time, footprint, resolution, viewing geometry and quality flags. A vessel can appear repeatedly across passes. Optical cloud screening has no direct radar equivalent; radar has its own sea-state and geometry limitations."),
        code('''
        sensors=pd.DataFrame([
          ["Sentinel-1 SAR","Active microwave backscatter","Day/night, cloud tolerant","Speckle, sea state, geometry; not all small vessels"],
          ["Sentinel-2 optical","Reflected sunlight","Shape, wakes, coastal context","Cloud, sun, spatial resolution"],
          ["VIIRS night lights","Low-light radiance","Some brightly lit fleets","Moon/cloud screening, unlit vessels"],
          ["SST products","Surface temperature estimate","Environmental context","Cloud/gap-filling, skin vs bulk; no pathogen diagnosis"],
          ["Ocean color","Optical water properties","Phytoplankton context","Cloud, turbidity, retrieval error; not toxin identity"]
        ],columns=["source","measurement","strength","limitation"])
        display(sensors)
        '''),
        md("## From catalog to calibrated crop\nUse the repository's optional local `fetch_sar_window.py` after installing `requirements-eo.txt`. The script requests a fresh short-lived signature, reads a bounded window, and saves unsigned provenance. Full-resolution geospatial processing needs libraries and resources beyond the core browser exercises.\n\n**Try it:** search a short interval, record the exact item IDs, and inspect polarization, orbit and mode before comparing images. Give one reason that an empty catalog result cannot establish an empty sea.")
    ])
    notebook("06_environment_and_health", "06 · Shared seasonality can look like a health signal", '''
    **Evidence: a real NOAA SST analysis series, followed by a separate synthetic environmental/effort experiment.** First inspect the observed temperature context and its provider uncertainty; then explore why correlations can arise without a causal relationship. No disease cases or observed chlorophyll data are included.

    Data: [NOAA NCEI OISST v2.1, final](https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.html), distributed by NOAA CoastWatch ERDDAP; free use and redistribution under the provider's recorded terms. Scientific context: [CDC on warming coastal waters and Vibrio](https://www.cdc.gov/han/2023/han00497.html); [NASA ocean-color context](https://www.earthdata.nasa.gov/s3fs-public/2024-07/SNWG%20Water%20Quality%20Fact%20Sheet.pdf). Temperature and chlorophyll are contextual indicators, not diagnoses of pathogens or toxins.
    ''', [
        md("## Observed environmental context\nThis 2024 daily series is one 0.25° cell at 54.625°N, 12.125°E in the Baltic, north of Rostock. OISST blends satellite and in situ measurements into a spatially complete analysis; it is not a direct cloud-free observation every day. Shading shows the provider-estimated **±1 standard deviation**, not a confidence interval or the full uncertainty of local conditions. The year differs from the 2017–2021 vessel study, so these layers are not used to infer a contemporaneous fishing-health association."),
        code('''
        sst=pd.read_csv(lab.DATA/"noaa_oisst_2024_point.csv",parse_dates=["time"])
        record=json.loads((lab.DATA/"noaa_oisst.provenance.json").read_text())
        display(sst.head())
        fig,ax=plt.subplots()
        daily=sst.set_index("time").reindex(pd.date_range(sst.time.min(),sst.time.max(),freq="D"))
        ax.plot(daily.index,daily.sst,color="#087e83",label="OISST analysis")
        ax.fill_between(daily.index,daily.sst-daily.err,daily.sst+daily.err,color="#087e83",alpha=.22,label="Provider ±1 SD")
        ax.set(xlabel="UTC date in 2024",ylabel="Sea-surface temperature (°C)",title="OBSERVED NOAA OISST PRODUCT | one Baltic grid cell")
        ax.legend();plt.show()
        print(record["attribution"])
        print("Missing archive dates (not imputed):",record["missing_dates_utc"])
        '''),
        md("## Now switch to a synthetic experiment\nThe following 120 months are invented, including SST, chlorophyll and effort. They are not derived from the NOAA series. A shared seasonal cycle and trend create a correlation even though the simulation contains no causal effect of effort on temperature or disease."),
        code('''
        env=lab.environment()
        display(env.head())
        fig,axes=plt.subplots(3,1,sharex=True,figsize=(11,7),constrained_layout=True)
        for ax,col,label,color in zip(axes,["sst_c","chlorophyll_mg_m3","effort_hours"],
            ["SST (°C)","Chlorophyll (mg/m³)","Effort (hours)"],["#bd6e13","#087e83","#4c6a99"]):
            ax.plot(env.month,env[col],color=color);ax.set_ylabel(label)
        axes[0].set_title("SYNTHETIC SERIES | shared seasons and trends")
        axes[-1].set_xlabel("Model month");plt.show()
        '''),
        md("## Change the comparison\nBoth effort and temperature were constructed with a seasonal cycle and time trend. Regress each on a constant, linear time, and annual sine/cosine terms, then compare the residuals. This is a confounding demonstration, not a recommended epidemiological model or a proof that all confounding has been removed."),
        code('''
        t=env.month.to_numpy()
        X=np.column_stack([np.ones(len(t)),t,np.sin(2*np.pi*t/12),np.cos(2*np.pi*t/12)])
        residuals={}
        for key in ["sst_c","effort_hours"]:
            coefficients=np.linalg.lstsq(X,env[key],rcond=None)[0]
            residuals[key]=env[key]-X@coefficients
        raw=env[["sst_c","effort_hours"]].corr().iloc[0,1]
        adjusted=pd.DataFrame(residuals).corr().iloc[0,1]
        display(pd.Series({"raw_correlation":raw,"after_removing_constructed_shared_terms":adjusted}))
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        axes[0].scatter(env.sst_c,env.effort_hours,s=15,c=t,cmap="viridis")
        axes[0].set(xlabel="Synthetic SST (°C)",ylabel="Synthetic effort (hours)",title="Raw values")
        axes[1].scatter(residuals["sst_c"],residuals["effort_hours"],s=15,color="#087e83")
        axes[1].set(xlabel="SST residual (°C)",ylabel="Effort residual (hours)",title="After seasonal/trend adjustment")
        fig.suptitle("SYNTHETIC CONFOUNDING | association depends on the question");plt.tight_layout();plt.show()
        '''),
        md("## Design a real One Health extension\nA Vibrio study would need environmental measurements, appropriate salinity and exposure information, case definitions, population denominators, care-seeking and reporting context, and ethical governance. A harmful-algal-bloom study needs species or toxin evidence. A mercury study needs contaminant sampling and consumption information. An offshore activity map supplies none of those outcomes by itself.\n\n**Try it:** remove the trend term from `X`. Then remove the seasonal terms. Explain how each choice changes the residual association. Identify a time lag you would justify biologically before looking at an outcome.")
    ])
    notebook("07_food_and_equity", "07 · Follow the food, not just the fleet", '''
    **Evidence: synthetic food-accounting scenarios.** Hold catch constant while changing distribution and losses. The model estimates potential edible availability, not intake, clinical benefit or dietary adequacy.

    Context: [FAO/WHO risks and benefits of fish consumption](https://www.who.int/publications/i/item/9789240096882) and [WHO One Health](https://www.who.int/publications/m/item/one-health-definitions-and-principles). The protein fraction below is an illustrative assumption, not species composition data.
    ''', [
        md("## Put units into the pathway\nPotential edible kilograms = catch tonnes × 1000 × local retention × edible fraction × (1 − loss). Divide by population and days, then convert kilograms to grams. This accounting includes no trade imports, household allocation, seasonality, or dietary substitution."),
        code('''
        RETENTION=.45
        EDIBLE_FRACTION=.65
        LOSS=.15
        result=lab.food_scenario(retention=RETENTION,edible_fraction=EDIBLE_FRACTION,loss=LOSS)
        display(pd.Series(result))
        rows=[]
        for retention in [.2,.45,.7]:
            for loss in [.05,.15,.3]:
                rows.append({"retention":retention,"loss":loss,**lab.food_scenario(retention=retention,loss=loss)})
        scenarios=pd.DataFrame(rows)
        display(scenarios.round(2))
        '''),
        code('''
        table=scenarios.pivot(index="loss",columns="retention",values="grams_per_person_per_day")
        fig,ax=plt.subplots()
        p=ax.imshow(table.to_numpy(),cmap="viridis",aspect="auto")
        ax.set_xticks(range(len(table.columns)),[f"{x:.0%}" for x in table.columns])
        ax.set_yticks(range(len(table.index)),[f"{x:.0%}" for x in table.index])
        for i in range(len(table.index)):
            for j in range(len(table.columns)):
                ax.text(j,i,f"{table.iloc[i,j]:.1f}",ha="center",va="center",color="white" if table.iloc[i,j]<10 else "black",fontweight="bold")
        ax.set(xlabel="Locally retained fraction",ylabel="Loss fraction",title="SYNTHETIC FOOD SYSTEM | same catch, different potential availability")
        fig.colorbar(p,ax=ax,label="Potential edible seafood (g/person/day)")
        plt.show()
        '''),
        md("## Who experiences the average?\nAn equal-per-person average is not evidence of equal access. The same regional availability can coexist with severe household differences in income, prices, storage, landings access, age, gender and cultural preferences. Fishing workers can also face exposure and safety risks that a food total hides."),
        code('''
        # Invented allocation: 20% of the population receives 60% of local edible supply.
        total=result["edible_kg"]
        allocation=pd.DataFrame({"group":["A","B"],"population":[20000,80000],"supply_share":[.60,.40]})
        allocation["available_g_person_day"]=total*allocation.supply_share*1000/allocation.population/365
        display(allocation)
        print("Synthetic allocation only; groups are not real demographic categories.")
        '''),
        md("## A decision that needs more evidence\nReducing losses may increase availability, but intervention cost, worker conditions, energy requirements and food safety also matter. Greater local retention may change earnings and trade relationships. Communities should help define the objective.\n\n**Try it:** choose two interventions that produce similar average availability. Identify how their distributional effects and costs could differ. State which household or market measurements you would collect before choosing between them.")
    ])
    notebook("08_fish_stocks", "08 · Fishing pressure, stock resilience and recovery", '''
    **Evidence: a published FAO summary and a separate synthetic biomass model.** Distinguish a stock assessment from a vessel activity map, and explore why growth and fishing mortality jointly shape recovery.

    Source for observed summary: [FAO 2025 marine fish-stock assessment](https://www.fao.org/newsroom/detail/fao-releases-the-most-detailed-global-assessment-of-marine-fish-stocks-to-date). These figures describe that assessment, not an automatically updated estimate.
    ''', [
        md("## Two true percentages with different denominators\nFAO's 2025 review reports 64.5% of assessed stocks at biologically sustainable levels and 77.2% of landings from biologically sustainable stocks when weighted by production. A stock-count percentage and a production-weighted percentage answer different questions. The assessment covers 2,570 stocks; it should not be mechanically appended to earlier assessment series without checking methodology."),
        code('''
        fao=json.loads((lab.DATA/"fao_2025_summary.json").read_text())
        summary=pd.DataFrame({"indicator":["Stock-count share","Production-weighted landings share"],"sustainable_percent":[fao["sustainable_stock_count_percent"],fao["sustainable_production_weighted_landings_percent"]]})
        display(summary)
        ax=summary.plot.barh(x="indicator",y="sustainable_percent",color=["#087e83","#bd6e13"],legend=False)
        ax.set(xlim=(0,100),xlabel="Percent (%)",ylabel="Denominator",title="OBSERVED FAO 2025 SUMMARY | denominators matter")
        for y,v in enumerate(summary.sustainable_percent):ax.text(v+1,y,f"{v}%",va="center")
        plt.tight_layout();plt.show()
        '''),
        md("## A deliberately simple population model\nWe use logistic growth with proportional fishing mortality:\n\n`dB/dt = r B (1 − B/K) − F B`.\n\n`B` is biomass, `r` intrinsic growth per year, `K` carrying capacity, and `F` fishing mortality per year. The model uses illustrative units. Apparent fishing hours are not `F`; converting effort to mortality would require catchability and species-specific evidence."),
        code("lab.show(lab.stock_slider())"),
        md("## More unobserved effort is an assumption to test\nIf total mortality were proportional to total effort, then `F_total = F_observed / (1 − hidden_share)`. That proportionality is a hypothetical scenario, not an inference from SAR unmatched fractions. The unmatched fractions in this book must not be substituted directly for `hidden_share`. Catchability, gear, species and behavior can differ."),
        code('''
        F_OBSERVED=.15
        fig,ax=plt.subplots()
        for share in [0,.25,.50,.70]:
            F_total=F_OBSERVED/(1-share)
            t,b=lab.stock_model(fishing_mortality=F_total)
            ax.plot(t,b,label=f"Hypothetical hidden effort {share:.0%}; F={F_total:.2f}")
        ax.set(xlabel="Model year",ylabel="Biomass (illustrative units)",title="SYNTHETIC SCENARIOS | an assumption changes the trajectory")
        ax.legend();plt.show()
        '''),
        md("## Recovery has conditions\nIn this model, a positive equilibrium exists when `F < r` and equals `K(1 − F/r)`. The model's maximum sustainable yield occurs at `B = K/2` and `F = r/2`. Those formulas are not management advice for a real stock. Real systems need uncertainty, stock structure, recruitment, climate, species interactions and socioeconomic evidence.\n\n**Try it:** change `r` and initial biomass while holding `F` fixed. Then design a recovery scenario with a timed mortality reduction. Explain why improved vessel visibility alone does not guarantee recovery, nutrition, or fair access.")
    ])
    notebook("09_gfw_workbench", "09 · Bring your Global Fishing Watch export", '''
    **Evidence: a synthetic schema example by default; your own real export only when you supply it.** This workbench shows how to inspect and map apparent fishing hours without placing an API token in a public notebook.

    Sources: [GFW download guidance](https://globalfishingwatch.org/faqs/how-can-i-obtain-global-fishing-watch-data-or-code/), [4Wings report fields](https://api-doc.globalfishingwatch.org/our-apis/documentation/docs/v3/4wings/report), [current terms](https://globalfishingwatch.org/terms-of-use/). Current GFW platform terms are distinct from the CC BY 4.0 publication data used elsewhere in this book.
    ''', [
        md("## Obtain a bounded export\nOpen the GFW map, choose a small region and time interval, and download a spatially resolved apparent-fishing-activity CSV. Extract downloaded archives first, keeping the caveat and citation files. Alternatively use a versioned static download. Upload the CSV through the lab file browser. API report and static-file column names differ; inspect your file and select the explicit mapping below. Do not put an API token into notebook cells, outputs, query strings or Git commits."),
        code('''
        USE_DEMO=True
        YOUR_CSV="data/private/my_gfw_export.csv"
        # Canonical mapping for a 4Wings spatial report; edit for the actual file.
        COLUMNS={"lat":"lat","lon":"lon","hours":"hours"}
        # Static portal files may use cell_ll_lat, cell_ll_lon and fishing_hours.
        # For those, use a mapping and explicitly set CELL_SIZE_DEGREES from its metadata.
        CELL_SIZE_DEGREES=None  # None means incoming coordinates are already cell centers.
        if USE_DEMO:
            raw=pd.DataFrame({"lat":[54.1,54.2,54.3,54.2],"lon":[12.0,12.1,12.2,12.3],"hours":[1.5,3.0,2.0,4.5]})
            label="SYNTHETIC SCHEMA EXAMPLE — not a GFW observation"
        else:
            raw=pd.read_csv(YOUR_CSV)
            label="USER-SUPPLIED EXPORT — record source, dataset version, period and license below"
        print(label)
        display(raw.head())
        '''),
        md("## Validate before plotting\nReject missing, nonnumeric, negative or out-of-range values. Missing effort is not silently replaced by zero. If a file supplies lower-left cell coordinates, add half its **documented** cell size, rather than guessing a resolution. Grouped totals without spatial coordinates cannot be mapped with this adapter."),
        code('''
        def normalize_effort(frame,mapping,cell_size=None):
            required=[mapping[k] for k in ["lat","lon","hours"]]
            if not set(required).issubset(frame.columns):
                raise ValueError(f"Expected columns {required}; found {list(frame.columns)}")
            out=frame[required].copy();out.columns=["lat","lon","hours"]
            for column in out:out[column]=pd.to_numeric(out[column],errors="raise")
            if not np.isfinite(out.to_numpy()).all():raise ValueError("Missing or nonfinite values require explicit investigation")
            if cell_size is not None:
                if not 0<cell_size<=10:raise ValueError("Supply a documented positive grid size in degrees")
                out[["lat","lon"]]+=cell_size/2
            if not out.lat.between(-90,90).all() or not out.lon.between(-180,180).all():raise ValueError("Coordinates outside WGS84 ranges")
            if (out.hours<0).any():raise ValueError("Negative apparent fishing hours")
            return out
        effort=normalize_effort(raw,COLUMNS,CELL_SIZE_DEGREES)
        display(effort)
        print("Total apparent fishing hours in this table:",effort.hours.sum())
        fig,ax=plt.subplots()
        p=ax.scatter(effort.lon,effort.lat,c=effort.hours,s=70,cmap="viridis",marker="s")
        ax.set(xlabel="Longitude (°)",ylabel="Latitude (°)",title=label)
        fig.colorbar(p,ax=ax,label="Apparent fishing hours");plt.show()
        '''),
        md("## Keep a source record with the result\nWhen using real data, replace the placeholders below before sharing. Dataset aliases such as `latest` can move; record the resolved version and retrieval date. Do not redistribute a provider export without checking its license and any restrictions in its accompanying caveat file."),
        code('''
        source_record={"mode":"synthetic" if USE_DEMO else "user-supplied",
            "provider":"teaching example" if USE_DEMO else "Global Fishing Watch",
            "dataset_version":"not applicable" if USE_DEMO else "REQUIRED: resolved dataset version",
            "period":"invented" if USE_DEMO else "REQUIRED: observation interval",
            "retrieval_date":"not applicable" if USE_DEMO else "REQUIRED: YYYY-MM-DD",
            "license":"original teaching example" if USE_DEMO else "REQUIRED: export-specific license",
            "coordinate_semantics":"cell centers" if CELL_SIZE_DEGREES is None else f"SW corner + {CELL_SIZE_DEGREES/2}°"}
        display(pd.Series(source_record))
        '''),
        md("**Next question:** compare your effort layer with the SAR study only after aligning periods, spatial support and units. The bundled SAR record ends in 2021 and measures normalized presence. An effort export measures modeled hours. Their numerical values cannot be subtracted to estimate hidden fishing hours.\n\nFor larger authenticated workflows, use the [official GFW Python client](https://github.com/GlobalFishingWatch/gfw-api-python-client) in a local or managed environment with secret handling outside notebook outputs.")
    ])
    print("Authored selected notebooks" if SELECTED else "Authored nine notebooks")


if __name__ == "__main__":
    main()
