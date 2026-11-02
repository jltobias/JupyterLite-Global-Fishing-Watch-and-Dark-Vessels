"""Optional local-only calibrated Sentinel-1 window extraction.

Requires requirements-eo.txt. Uses HTTP range reads; never loads a whole scene.
No authentication token is written to disk or printed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import requests
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content/data"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lon", type=float, default=12.09)
    p.add_argument("--lat", type=float, default=54.165)
    p.add_argument("--item-index", type=int, default=1, help="Index in bundled STAC snapshot")
    p.add_argument("--size", type=int, default=512)
    p.add_argument("--ca-bundle", help="Optional organization CA bundle for GDAL HTTPS")
    args = p.parse_args()
    if not 32 <= args.size <= 1024:
        p.error("Window size must be between 32 and 1024 pixels")
    snapshot = json.loads((DATA / "sentinel1_stac_snapshot.json").read_text())
    item = snapshot["features"][args.item_index]
    href = item["assets"]["vv"]["href"]
    response = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/sign",
                            params={"href": href}, timeout=60)
    response.raise_for_status()
    signed_href = response.json()["href"]
    env = {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tiff,.tif",
           "GDAL_HTTP_TIMEOUT": "60", "GDAL_HTTP_MAX_RETRY": "2"}
    if args.ca_bundle:
        env["GDAL_HTTP_CA_BUNDLE"] = args.ca_bundle
    # Do not expose temporary SAS URLs via exception messages.
    try:
        with rasterio.Env(**env), rasterio.open(signed_href) as src:
            xs, ys = transform("EPSG:4326", src.crs, [args.lon], [args.lat])
            row, col = src.index(xs[0], ys[0])
            half = args.size // 2
            window = Window(col-half, row-half, args.size, args.size)
            if window.col_off < 0 or window.row_off < 0 or window.col_off+args.size > src.width or window.row_off+args.size > src.height:
                raise ValueError("Requested center lies outside this scene; select another item")
            data = src.read(1, window=window, masked=True).filled(np.nan).astype("float32")
            data[data <= 0] = np.nan
            if not np.isfinite(data).any():
                raise ValueError("Window contains no positive valid pixels")
            affine = list(src.window_transform(window))
            crs = src.crs.to_string()
            bounds = list(rasterio.windows.bounds(window, src.transform))
    except rasterio.errors.RasterioError as exc:
        raise RuntimeError("Remote raster read failed; check scene access, network and CA trust. Temporary asset URL suppressed.") from None
    target = DATA / "sentinel1_real_window.npz"
    np.savez_compressed(target, gamma0_linear=data)
    provenance = {"file": target.name, "item_id": item["id"], "collection": "sentinel-1-rtc",
        "acquired": item["properties"]["datetime"], "retrieved": datetime.now(timezone.utc).date().isoformat(), "retrieval_date_timezone": "UTC",
        "asset_href_unsigned": href, "band": "vv", "units": "linear gamma0 backscatter",
        "transformation": "Window read at source pixel spacing; nodata/nonpositive -> NaN; no resampling",
        "crs": crs, "transform": affine, "bounds_in_crs": bounds, "center_lon_lat": [args.lon, args.lat],
        "shape": list(data.shape), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "attribution": "Contains modified Copernicus Sentinel data (2024), processed by Microsoft Planetary Computer.",
        "license_url": "https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice",
        "note": "Actual calibrated radar pixels. No vessel labels, AIS matches or validated detections are supplied."}
    (DATA / "sentinel1_real_window.provenance.json").write_text(json.dumps(provenance, indent=2)+"\n", encoding="utf-8")
    print(f"Saved {data.shape} real radar window; valid fraction: {np.isfinite(data).mean():.3f}")


if __name__ == "__main__":
    main()
