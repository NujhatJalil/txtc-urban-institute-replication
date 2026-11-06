# 01_prepare_fema_declarations.py

from datetime import date
from pathlib import Path
import config
import pandas as pd

def refresh_fema_declarations(dir=config.DATA_DIR, overwrite=False):
    dir.mkdir(parents = True, exist_ok = True)

    snapshot_date = date.today().strftime("%Y_%m_%d")
    out_path = dir / f"DisasterDeclarationsSummaries_{snapshot_date}.parquet"

    if out_path.exists() and not overwrite:
        print(f"Snapshot already exists at {out_path}")
        return out_path

    declarations = # todo