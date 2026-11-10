# 01_prepare_fema_declarations.py

from datetime import date
from pathlib import Path
import config
import requests
import janitor
import pandas as pd

def refresh_fema_declarations(box_dir=config.OPENFEMA_DIR, overwrite=False):
    box_dir.mkdir(parents = True, exist_ok = True)

    snapshot_date = date.today().strftime("%Y_%m_%d")
    out_path = box_dir / f"DisasterDeclarationsSummaries_{snapshot_date}.parquet"

    if out_path.exists() and not overwrite:
        print(f"Snapshot already exists at {out_path}")
        return out_path

    url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"

    params = {"$filter": "declarationType eq 'DR'"}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        results = response.json().get("DisasterDeclarationsSummaries", [])
        declarations = pd.DataFrame(results)
        declarations = declarations.clean_names(case_type="snake")
        declarations.to_parquet(out_path, index=False)
    else:
        print(f"Failed to fetch data: {response.status_code}")


def get_fema_declarations(refresh=False, as_of=None, box_dir=config.OPENFEMA_DIR):
    box_dir.mkdir(parents = True, exist_ok = True)

    if refresh:
        refresh_fema_declarations(box_dir)

    snapshots = []

    for path in box_dir.glob("DisasterDeclarationsSummaries_*.parquet"):
        date_text = path.stem.replace("DisasterDeclarationsSummaries_","")
        snapshot_date = pd.to_datetime(date_text, format="%Y_%m_%d")
        snapshots.append((snapshot_date, path))

    if not snapshots:
        raise FileNotFoundError(f"No FEMA snapshots found in {box_dir}")

    if as_of is not None:
        as_of = pd.Timestamp(as_of)

        snapshots = [
            item for item in snapshots if item[0] <= as_of
        ]

    if not snapshots:
        raise ValueError(f"No FEMA snapshot on or before {as_of}")

    snapshot_date, selected_path = max(snapshots, key=lambda item: item[0])

    print(f"Loading FEMA snapshot from {snapshot_date}")
    return pd.read_parquet(selected_path)