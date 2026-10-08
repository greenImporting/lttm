"""calls tfl apis to get status about lines and stations, then
cleans and removes unnecessary data. exposes a function to 
give all data nicely formatted

rewritten"""

import time
import requests
import json
import config as cfg

_key_idx = 0 # key index
SESSION = requests.Session()


def current_key():
    return cfg.KEYS[_key_idx]

def swap_key():
    global _key_idx
    _key_idx = (_key_idx + 1) % len(cfg.KEYS)

def call(endpoint, **params):
    url = endpoint.format(**params)
    last_r = None

    for attempt in range(len(cfg.KEYS) * 2): # some more tries
        key = current_key()
        if not key:
            raise RuntimeError("MISSING TFL API KEY! SET IN .env")

        try:
            r = SESSION.get(url, params={"app_key": current_key()}, timeout=6)
            last_r = r

            if r.status_code == 200:
                return r
            
            if r.status_code == 429:
                r_a = r.headers.get("Retry-After")
                delay = int(r_a) if r_a and r_a.isdigit() else 1
                cfg.logger.info(f"error 429, retrying after {delay}")
                time.sleep(delay)
                swap_key()
                continue

            cfg.logger.warning(f"tfl {r.status_code}, retrying.")

        except requests.RequestException as e:
            delay = (attempt + 1) * 0.5
            cfg.logger.warning(f"tfl request failed ({e}), retrying in {delay}")
            time.sleep(delay)
            
    return last_r

def bulk_station_distruptions(ids, chunk=20):
    output = []
    for i in range(0, len(ids), chunk):
        batch = ids[i:i + chunk] #slice i up to but not including i + chunk. ~30 calls
        r = call(cfg.STATIONS_BULK_EP, stationId=",".join(batch))

        if r.status_code == 200:
            output.extend(r.json())
    return output

def line_statuses():
    r = call(cfg.LINE_STATUS_EP)
    return json.dumps(r.json(), indent=2)

def station_statuses():
    r = bulk_station_distruptions(cfg.station_ids)
    return json.dumps(r, indent=2)
