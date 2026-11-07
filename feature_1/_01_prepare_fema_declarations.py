# 01_prepare_fema_declarations.py

from datetime import date
from pathlib import Path
import config
import requests
import pandas as pd

def refresh_fema_declarations(dir=config.OPENFEMA_DIR, overwrite=False):
    dir.mkdir(parents = True, exist_ok = True)

    snapshot_date = date.today().strftime("%Y_%m_%d")
    out_path = dir / f"DisasterDeclarationsSummaries_{snapshot_date}.parquet"

    if out_path.exists() and not overwrite:
        print(f"Snapshot already exists at {out_path}")
        return out_path

    url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"

    params = {"$filter": "declarationType eq 'DR'"}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        results = response.json().get("DisasterDeclarationsSummaries", [])
        declarations = pd.DataFrame(results)
        declarations.to_parquet(out_path, index=False)
    else:
        print(f"Failed to fetch data: {response.status_code}")