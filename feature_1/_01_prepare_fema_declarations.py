# 01_prepare_fema_declarations.py

from datetime import date
from pathlib import Path
import config
import requests
import janitor
import pandas as pd
import numpy as np

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

def classify_declarations(declarations, year_range=None, natural_hazards=None):

    if year_range is None:
        year_range = list(range(2023,2025))

    if natural_hazards is None:
        natural_hazards = [
            "Fire", "Flood", "Hurricane", "Severe Storm", "Winter Storm", "Tornado",
            "Snowstorm", "Earthquake", "Mud/Landslide", "Coastal Storm",
            "Severe Ice Storm", "Tropical Storm", "Typhoon", "Volcanic Eruption",
            "Tsunami", "Freezing", "Drought", "Tropical Depression",
            "Straight-Line Winds"
        ]

    known_non_natural = [
        "Biological", "Dam/Levee Break", "Terrorist", "Human Cause", "Toxic Substances",
        "Fishing Losses", "Other"
    ]

    classified1 = declarations.loc[declarations["declaration_type"] == "DR"].copy()
    classified1["incident_type"] = np.select(
        [
            (classified1["incident_type"] == "Other")
            & classified1["declaration_title"].str.contains("STRAIGHT-LINE WINDS", na=False),
            (classified1["incident_type"] == "Other")
            & classified1["declaration_title"].str.contains("WIND STORM", na=False),
            (classified1["incident_type"] == "Other")
            & classified1["declaration_title"].str.contains(
                "SEVERE WEATHER CONDITIONS", na=False
            ),
        ],
        ["Straight-Line Winds", "Straight-Line Winds", "Severe Storm"],
        default=classified1["incident_type"],
    )

    classified1["calendar_year_declared"] = pd.to_datetime(classified1["declaration_date"]).dt.year
    classified1["county_fips"] = (classified1["fips_state_code"].astype("string") + classified1["fips_county_code"].astype("string"))

    retired_fips_list = [
        "46113", "46102", # Shannon County SD -> Oglala Lakota County (Pine Ridge)
        "51515", "51019", # Bedford (independent) City VA -> Bedford County
        "02270", "02158", # Wade Hampton Census Area AK -> Kusilvak Census Area
        "02201", "02198", # Prince of Wales-Outer Ketchikan AK -> Prince of Wales-Hyder,
        "02201", "02130", #   Ketchikan Gateway Borough (annexed Outer Ketchikan parts),
        "02201", "02275", #   and Wrangell City and Borough (Meyers Chuck area)
        "02280", "02195", # Wrangell-Petersburg Census Area AK -> Petersburg Borough
        "02280", "02275", #   and Wrangell City and Borough
        "09001", "09120", # Fairfield CT -> Greater Bridgeport,
        "09001", "09140", #   Naugatuck Valley (Shelton),
        "09001", "09190", #   and Western CT
        "09003", "09110", # Hartford CT -> Capitol
        "09003", "09140", #   and Naugatuck Valley (Bristol, Plainville, Plymouth)
        "09005", "09160", # Litchfield CT -> Northwest Hills,
        "09005", "09140", #   Naugatuck Valley (Thomaston, Watertown),
        "09005", "09190", #   and Western CT (New Milford, Sherman)
        "09007", "09130", # Middlesex CT -> Lower CT River Valley
        "09009", "09170", # New Haven CT -> South Central CT
        "09009", "09140", #   and Naugatuck Valley (Waterbury, Naugatuck)
        "09011", "09180", # New London CT -> Southeastern CT
        "09013", "09110", # Tolland CT -> Capitol
        "09013", "09150", #   and Northeastern CT (Union)
        "09015", "09150"
        ]
    retired_fips_lookup = pd.DataFrame({
        "retired_fips": retired_fips_list[::2],
        "current_fips": retired_fips_list[1::2]
    })