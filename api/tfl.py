"""
communicates and filters with apis to recieve
each station/line data, then exposes through 
an all line status func. for another file to 
deal with it 🤣!!!!
"""
import os
import requests
import logging
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DP = Path("data/") # datapath

lines = json.loads((DP / "_lines.json").read_text())
stations = json.loads((DP / "_stations.json").read_text())
s2l = json.loads((DP / "_station_lines.json").read_text())

station_ids= list(stations.keys())
# _stations is already deduped. if aint broke dont fix 


# stations["910GEMRSPKH"]["common_name"]      # "Emerson Park Rail Station"
# lines["weaver"]["station_order"]            # ordered station ids
# s2l["910GEMRSPKH"]                          # ["liberty"]

KEYS = [os.getenv("PRIMARY_API_KEY"), os.getenv("SECONDARY_API_KEY")]
_key_idx = 0
# prim and secdry key
BASE = "https://api.tfl.gov.uk"

modes = ["tube", "dlr", "elizabeth-line", "overground", "tram"]
modes_str = ",".join(modes)

STATUS_EP = f"{BASE}/Line/Mode/{modes_str}/Status"
BULK_EP = f"{BASE}/StopPoint/{{stationId}}/Disruption"
# notes: status of whole line and each station within line. mass api + update

def current_key():
    return KEYS[_key_idx]

def switch_keys():
    global _key_idx
    _key_idx = (_key_idx + 1) % len(KEYS) # even=prim, odd=sec

def call(endpoint, **params):
    url = endpoint.format(**params)
    for attempt in range(len(KEYS)): # only loop through twice bc of 2 keys
        try:
            r = requests.get(url, params={"app_key": current_key()}, timeout=5)
            if r.status_code != 429: #TODO: better exception handling
                return r
            retry_after_h = r.headers.get("Retry-After")
            if retry_after_h and retry_after_h.isdigit():# if header returns a retry header w/ a number
                ra = int(retry_after_h)
                logger.info(f"retrying after {ra}") 
                time.sleep(ra)
            switch_keys()
        except requests.RequestException as e:
            logger.warning("request failed: %s", e, exc_info=True)
    print(f"gave up after {len(KEYS)} attempts")
    return r 

def bulk_call(ids, chunk=20):
    response = []
    for i in range(0, len(ids), chunk):
        batch = ids[i:i+ chunk] # slice me up. i up to (notincluding) i+chunk. takes 20 ids at a time, so ~550 calls to ~30 calls
        r = call(BULK_EP, stationId=",".join(batch)) 
        if r.status_code == 200 and r.json():
            response.extend(r.json())
    return response
    
def status_clean(line):
    return {
        "id": line.get("id"),
        "lineStatuses": [
            {
                "statusSeverity": stati.get("statusSeverity"),
                "statusSeverityDescription": stati.get("statusSeverityDescription"),
                **({"reason": stati["reason"]} if stati.get("reason") else {}) # adds reason if reason is present, else return nish
            }
            for stati in line.get("lineStatuses", [])
        ]
    }

def pamper_all_statuses():
    r = call(status_EP)
    return [status_clean(i) for i in r.json()] #builds and returns the whole list of line stati


def show_all_goodies():
    # return json.dumps(pamper_all_statuses(), indent=2)
    return 


logger.info("loaded tfl")

print(bulk_call(station_ids))