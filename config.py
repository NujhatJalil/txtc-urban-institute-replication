# config.py

import os
from pathlib import Path
from dotenv import load_dotenv



PROJECT_ROOT = Path(__file__).resolve().parent


DATA_DIR = PROJECT_ROOT/"data"
OPENFEMA_DIR = DATA_DIR/"openfema"

# keys
load_dotenv()
