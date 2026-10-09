from dotenv import load_dotenv
import os
import json
import logging
from pathlib import Path

load_dotenv()

DP = Path("data/")


logger = logging.getLogger(__name__)
lines = json.loads((DP / "_lines.json").read_text())
stations = json.loads((DP / "_stations.json").read_text())
s2l = json.loads((DP / "_station_lines.json").read_text())
station_ids= list(stations.keys())
modes = ["tube", "dlr", "elizabeth-line", "overground", "tram"]
modes_str = ",".join(modes)

KEYS = [os.getenv("PRIMARY_API_KEY"), os.getenv("SECONDARY_API_KEY")]
BASE = "https://api.tfl.gov.uk"
LINE_STATUS_EP = f"{BASE}/Line/Mode/{modes_str}/Status"
STATIONS_BULK_EP = f"{BASE}/StopPoint/{{stationId}}/Disruption"