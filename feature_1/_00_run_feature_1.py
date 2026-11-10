## 00_run_feature_1.py— feature-1 pipeline entry point

from . import *
from pathlib import Path
import config
import requests
import pandas as pd

def main():
    print(get_fema_declarations(True).head())
    
if __name__ == "__main__":
    main()