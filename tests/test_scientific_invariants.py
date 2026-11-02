"""Check scientific/data failure modes rather than mirroring plotting code."""
from pathlib import Path
import hashlib
import json
import sys
import unittest
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"content"))
import oceanlab as lab


class ProvenanceTests(unittest.TestCase):
    def test_downloads_match_recorded_checksums(self):
        manifest=json.loads((lab.DATA/"download_manifest.json").read_text())
        self.assertEqual(manifest["license_url"],"https://creativecommons.org/licenses/by/4.0/")
        for item in manifest["files"]:
            payload=(lab.DATA/item["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(),item["sha256"])
            self.assertEqual(hashlib.md5(payload).hexdigest(),item["source_md5"])

    def test_derived_and_real_radar_provenance(self):
        for name,entry in json.loads((lab.DATA/"derived_manifest.json").read_text()).items():
            self.assertEqual(hashlib.sha256((lab.DATA/name).read_bytes()).hexdigest(),entry["sha256"])
        record=json.loads((lab.DATA/"sentinel1_real_window.provenance.json").read_text())
        self.assertEqual(hashlib.sha256((lab.DATA/record["file"]).read_bytes()).hexdigest(),record["sha256"])
        self.assertNotIn("sig=",record["asset_href_unsigned"])
        with np.load(lab.DATA/record["file"]) as a:
            self.assertEqual(list(a["gamma0_linear"].shape),record["shape"])
            self.assertGreater(np.isfinite(a["gamma0_linear"]).mean(),.9)

    def test_geographic_cells_and_components(self):
        d=lab.activity(full=True)
        self.assertEqual(len(d),139189)
        self.assertTrue(d.lon.between(-180,180).all())
        self.assertTrue(d.lat.between(-90,90).all())
        np.testing.assert_allclose((d.lon-.1)*5,np.round((d.lon-.1)*5),atol=1e-10)
        valid=d.dropna(subset=["AIS_fishing","dark_fishing","tot_fishing"])
        np.testing.assert_allclose(valid.AIS_fishing+valid.dark_fishing,valid.tot_fishing,rtol=1e-10,atol=1e-10)
        self.assertTrue((valid[["AIS_fishing","dark_fishing","tot_fishing"]]>=0).all().all())
        self.assertEqual(d.tot_fishing.isna().sum(),5)

    def test_observed_temperature_has_units_dates_and_checksums(self):
        record=json.loads((lab.DATA/"noaa_oisst.provenance.json").read_text())
        for item in record["files"]:
            self.assertEqual(hashlib.sha256((lab.DATA/item["file"]).read_bytes()).hexdigest(),item["sha256"])
        d=pd.read_csv(lab.DATA/"noaa_oisst_2024_point.csv")
        self.assertEqual(len(d),record["rows"])
        self.assertGreaterEqual(len(d),350)
        self.assertTrue((d.err>=0).all())
        self.assertTrue(d.sst.between(-3,40).all())
        self.assertEqual(record["units"]["sst"],"degree_C")
        self.assertEqual(pd.to_datetime(d.time,utc=True).dt.year.unique().tolist(),[2024])
        self.assertEqual(len(d)+len(record["missing_dates_utc"]),366)


class MatchingTests(unittest.TestCase):
    def test_antimeridian_distance_is_short(self):
        self.assertAlmostEqual(float(lab.haversine_km(179.9,0,-179.9,0)),22.239,places=2)

    def test_identity_cannot_be_assigned_twice(self):
        detections=pd.DataFrame({"lon":[0.,.001],"lat":[0.,0.],"minute":[0.,0.]})
        ais=pd.DataFrame({"id":["A"],"lon":[0.],"lat":[0.],"minute":[0.]})
        out=lab.match_points(detections,ais)
        self.assertEqual(out.match.notna().sum(),1)
        self.assertEqual(out.match.isna().sum(),1)

    def test_invalid_time_and_empty_input_remain_unmatched(self):
        d=pd.DataFrame({"lon":[0.],"lat":[0.],"minute":[0.]})
        a=pd.DataFrame({"id":["A"],"lon":[0.],"lat":[0.],"minute":[100.]})
        self.assertTrue(lab.match_points(d,a).match.isna().all())
        self.assertTrue(lab.match_points(d,a.iloc[:0]).match.isna().all())
        self.assertTrue(lab.match_points(d.iloc[:0],a).empty)


class ModelTests(unittest.TestCase):
    def test_flat_ocean_and_land_do_not_create_targets(self):
        image=np.ones((40,40))*.01
        land=np.zeros_like(image,dtype=bool)
        land[:,:10]=True
        image[land]=1000
        candidates,_=lab.radar_detect(image,land)
        self.assertEqual(len(candidates),0)

    def test_duplicate_candidate_not_double_true_positive(self):
        result=lab.detection_metrics(np.array([[10,10],[10,11]]),np.array([[10,10]]))
        self.assertEqual((result["tp"],result["fp"],result["fn"]),(1,1,0))

    def test_stock_equilibrium_and_time_step(self):
        # For r=.4, F=.2, K=1000, the analytical equilibrium is 500.
        _,equilibrium=lab.stock_model(fishing_mortality=.2,B0=500)
        np.testing.assert_allclose(equilibrium,500,atol=1e-9)
        _,fine=lab.stock_model(fishing_mortality=.3,dt=.025)
        _,normal=lab.stock_model(fishing_mortality=.3,dt=.05)
        self.assertLess(abs(fine[-1]-normal[-1]),1)
        _,collapse=lab.stock_model(fishing_mortality=.6)
        self.assertTrue((collapse>=0).all())
        self.assertLess(collapse[-1],1)

    def test_food_mass_balance_and_invalid_inputs(self):
        result=lab.food_scenario(retention=1,edible_fraction=1,loss=0,catch_tonnes=365,population=1000)
        self.assertAlmostEqual(result["grams_per_person_per_day"],1000)
        self.assertEqual(lab.food_scenario(retention=0)["edible_kg"],0)
        with self.assertRaises(ValueError):lab.food_scenario(loss=1.1)
        with self.assertRaises(ValueError):lab.match_points(pd.DataFrame(),pd.DataFrame(),max_km=0)


if __name__=="__main__":unittest.main()
