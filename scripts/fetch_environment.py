"""Download one bounded NOAA OISST point series with uncertainty and provenance."""
from datetime import datetime,timezone
from io import StringIO
from pathlib import Path
import hashlib
import json
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"content/data"


def main():
    dataset="ncdcOisst21Agg_LonPM180"
    root="https://coastwatch.pfeg.noaa.gov/erddap"
    metadata=requests.get(f"{root}/info/{dataset}/index.json",timeout=60)
    metadata.raise_for_status()
    attrs={row[2]:row[4] for row in metadata.json()["table"]["rows"] if row[0]=="attribute" and row[1]=="NC_GLOBAL"}
    selection="[(2024-01-01T12:00:00Z):1:(2024-12-31T12:00:00Z)][(0.0)][(54.625)][(12.125)]"
    url=f"{root}/griddap/{dataset}.csv?sst{selection},err{selection}"
    response=requests.get(url,timeout=120)
    response.raise_for_status()
    frame=pd.read_csv(StringIO(response.text),skiprows=[1])
    if len(frame)<350 or frame[["sst","err"]].isna().any().any():
        raise ValueError("Expected a near-complete year of valid SST/error values; inspect provider response")
    dates=pd.to_datetime(frame.time,utc=True)
    expected=pd.date_range("2024-01-01T12:00:00Z","2024-12-31T12:00:00Z",freq="D")
    missing=[d.isoformat() for d in expected.difference(dates)]
    raw=DATA/"noaa_oisst_2024_point_raw.csv";raw.write_bytes(response.content)
    derived=DATA/"noaa_oisst_2024_point.csv";frame.to_csv(derived,index=False)
    record={"dataset":dataset,"product":"NOAA NCEI OISST v2.1 final, daily, 0.25 degree",
        "url":url,"metadata_url":metadata.url,"point_lat_lon":[54.625,12.125],"period":"2024-01-01/2024-12-31",
        "retrieved":datetime.now(timezone.utc).date().isoformat(),"retrieval_date_timezone":"UTC",
        "attribution":"NOAA National Centers for Environmental Information; distributed by NOAA CoastWatch ERDDAP",
        "license":attrs["license"],"rows":len(frame),"missing_dates_utc":missing,"units":{"sst":"degree_C","err":"degree_C"},
        "transformation":"ERDDAP point/time subset; normalized CSV removes units row only; no imputation or resampling",
        "caveat":"Interpolated/extrapolated analysis merging satellite and in situ observations; a complete field is not cloud-free direct observation. Error is provider-estimated standard deviation, not a confidence interval.",
        "files":[{"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in [raw,derived]]}
    (DATA/"noaa_oisst.provenance.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(f"Saved {len(frame)} observed-product SST values; temporal gaps retained: {missing}")


if __name__=="__main__":main()
