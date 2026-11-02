"""Derive small browser-ready data from verified source files; no network needed."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content/data"


def main():
    original = DATA / "raster_5th_degree.feather"
    frame = pd.read_feather(original)
    # The source indexes the SW corner at five times degrees. Map cell centers.
    frame["lat"] = frame.lat_index / 5 + .1
    frame["lon"] = frame.lon_index / 5 + .1
    fields = ["lat", "lon", "AIS_fishing", "dark_fishing", "tot_fishing",
              "AIS_nonfishing", "dark_nonfishing", "overpasses_2017_2021"]
    np.savez_compressed(DATA / "sar_activity_2017_2021.npz", **{key: frame[key].to_numpy() for key in fields})
    # Sum normalized cell activity, retaining missingness. This is a study proxy,
    # not unique vessels, fishing hours, or a count of illegal events.
    frame["lat_bin"] = np.floor(frame.lat)
    frame["lon_bin"] = np.floor(frame.lon)
    one = frame.groupby(["lat_bin", "lon_bin"])[["AIS_fishing", "dark_fishing", "tot_fishing"]].sum(min_count=1).reset_index()
    one["lat"] = one.lat_bin + .5
    one["lon"] = one.lon_bin + .5
    one.to_csv(DATA / "sar_activity_1deg.csv", index=False, float_format="%.7g")
    # A few source columns have misleading precomputed fraction names. Recompute
    # fractions transparently in the notebooks from named numerator/denominator.
    notes = {
        "sar_activity_2017_2021.npz": {"source": original.name,
            "transformation": "Selected columns; cell centers = index / 5 + 0.1; no imputation.",
            "rows": len(frame)},
        "sar_activity_1deg.csv": {"source": original.name,
            "transformation": "1-degree bins; sum of source per-overpass normalized cell activity; min_count=1; center = floor(degrees)+0.5.",
            "rows": len(one)},
    }
    for name, entry in notes.items():
        entry["sha256"] = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
        entry["license"] = "CC-BY-4.0"
        entry["doi"] = "10.6084/m9.figshare.24309475"
        entry["period"] = "2017-2021"
    (DATA / "derived_manifest.json").write_text(json.dumps(notes, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(frame):,} study cells and {len(one):,} map bins")


if __name__ == "__main__":
    main()
