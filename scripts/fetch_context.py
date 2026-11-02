"""Retrieve an open coastline and a reproducible EO metadata snapshot."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content/data"


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    # Pin Natural Earth to v5.1.2; no political boundaries are needed for these maps.
    url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_coastline.geojson"
    r = session.get(url, timeout=60)
    r.raise_for_status()
    (DATA / "coastline.geojson").write_bytes(r.content)
    provenance = {"file": "coastline.geojson", "source": "Natural Earth 1:110m coastline v5.1.2",
                  "url": url, "license": "Public domain", "retrieved": datetime.now(timezone.utc).date().isoformat(),
                  "sha256": hashlib.sha256(r.content).hexdigest()}
    query = {"collections": ["sentinel-1-rtc"], "bbox": [11.5, 54.0, 13.5, 55.0],
             "datetime": "2024-06-01T00:00:00Z/2024-06-30T23:59:59Z", "limit": 3}
    api = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
    r = session.post(api, json=query, timeout=90)
    r.raise_for_status()
    snapshot = r.json()
    if not snapshot.get("features"):
        raise ValueError("STAC query returned no scenes")
    # Unsigned asset references only. Never persist temporary SAS credentials.
    (DATA / "sentinel1_stac_snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    (DATA / "context_manifest.json").write_text(json.dumps({"coastline": provenance,
        "retrieval_date_timezone": "UTC", "stac": {"api": api, "query": query, "retrieved": datetime.now(timezone.utc).date().isoformat(),
                 "license": "See collection license and Copernicus Sentinel Data terms",
                 "note": "Metadata only, not radar pixels; links may require fresh signing."}}, indent=2) + "\n", encoding="utf-8")
    print(f"Saved coastline and {len(snapshot['features'])} Sentinel-1 metadata records")


if __name__ == "__main__":
    main()
