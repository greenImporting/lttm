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

status_EP = f"{BASE}/Line/Mode/{modes_str}/Status"
disruption_EP = f"{BASE}/StopPoint/{{stationId}}/Disruption"
# notes: status of whole line and each station within line. mass api + update

def current_key():
    return KEYS[_key_idx]

def switch_keys():
    global _key_idx
    _key_idx = (_key_idx + 1) % len(KEYS) # even=prim, odd=sec

def call(endpoint, **params):
    url = endpoint.format(**params)
    for attempt in range(len(KEYS)): # only loop through twice bc of 2 keys
        r = requests.get(url, params={"app_key": current_key()}, timeout=5)
        if r.status_code != 429: #TODO: better exception handling
            return r
        retry_after_h = r.headers.get("Retry-After")
        if retry_after_h and retry_after_h.isdigit():# if header returns a retry header w/ a number
            ra = int(retry_after_h)
            logger.info(f"retrying after {ra}") 
            time.sleep(ra)
        switch_keys()
    print(f"gave up after {len(KEYS)} attempts")
    return r 

def disruption_calls(endpoint, ids):
    responses = {}
    for i in ids:
        r = call(endpoint, stationId=i)
        responses[i] = r.json()
    return responses

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
    return [status_clean(i) for i in r.json()] #LOL, builds and returns the whole list of line statuses


def show_all_goodies():
    # return json.dumps(pamper_all_statuses(), indent=2)
    return disruption_calls(disruption_EP, station_ids)


logger.info("loaded tfl")