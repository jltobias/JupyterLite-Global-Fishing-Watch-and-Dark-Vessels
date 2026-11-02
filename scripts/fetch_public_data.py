"""Refresh small, attributed public teaching datasets. Network access is explicit."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import requests
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "content" / "data"


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "OceanWatch-OneHealth-educational-book/1.0"
    article = session.get("https://api.figshare.com/v2/articles/24309475", timeout=60)
    article.raise_for_status()
    meta = article.json()
    records = []
    wanted = {"raster_5th_degree.feather", "vessels_bycontinent_v20230803.csv",
              "vessel_barplots_v20230815.csv", "README.md"}
    for entry in meta["files"]:
        if entry["name"] not in wanted:
            continue
        if entry["id"] == 42699019:  # duplicate of the retained file 44031660
            continue
        response = session.get(entry["download_url"], timeout=120)
        response.raise_for_status()
        payload = response.content
        if hashlib.md5(payload).hexdigest() != entry["computed_md5"]:
            raise ValueError(f"Provider checksum mismatch: {entry['name']}")
        name = "paolo2024_README.md" if entry["name"] == "README.md" else entry["name"]
        (DATA / name).write_bytes(payload)
        records.append({"file": name, "source_file_id": entry["id"],
                        "url": entry["download_url"], "sha256": hashlib.sha256(payload).hexdigest(),
                        "source_md5": entry["computed_md5"], "bytes": len(payload),
                        "license": "CC-BY-4.0", "doi": "10.6084/m9.figshare.24309475"})
    # Keep the provider's exact immutable file identifiers, not a moving latest alias.
    (DATA / "download_manifest.json").write_text(json.dumps({
        "retrieved": datetime.now(timezone.utc).date().isoformat(), "retrieval_date_timezone": "UTC", "article_version": meta["version"],
        "citation": "Paolo et al. (2024). Satellite mapping reveals extensive industrial activity at sea. Nature 625, 85-91. doi:10.1038/s41586-023-06825-8",
        "license_url": meta["license"]["url"], "files": records}, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(records)} public files in {DATA}")


if __name__ == "__main__":
    main()
