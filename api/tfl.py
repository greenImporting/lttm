"""
calls tfl api using env keys for live line and station status and disruptions. 
exposes two functions station_statuses() and line_statuses 
"""

import time
import requests
from . import config as cfg

_key_idx = 0 # key index
SESSION = requests.Session()


def _current_key():
    if not cfg.KEYS:
        raise RuntimeError("MISSING TFL API KEY! SET IN .env")
    return cfg.KEYS[_key_idx]

def _swap_key():
    global _key_idx
    _key_idx = (_key_idx + 1) % len(cfg.KEYS)

def _call(endpoint, **params):
    url = endpoint.format(**params)
    last_r = None

    for attempt in range(len(cfg.KEYS) * 2): # some more tries
        key = _current_key()

        try:
            r = SESSION.get(url, params={"app_key": _current_key()}, timeout=6)
            last_r = r

            if r.status_code == 200:
                cfg.logger.info(f"response 200, with length of {len(r.json())}")
                return r
            
            if r.status_code == 429:
                r_a = r.headers.get("Retry-After")
                delay = int(r_a) if r_a and r_a.isdigit() else 1
                cfg.logger.info(f"error 429, retrying after {delay} seconds")
                time.sleep(delay)
                _swap_key()
                continue

            cfg.logger.warning(f"tfl returned {r.status_code}, retrying.")

        except requests.RequestException as e:
            delay = (attempt + 1) * 0.5
            cfg.logger.warning(f"tfl request failed ({e}), retrying in {delay}")
            time.sleep(delay)
            
    if last_r is not None:
        last_r.raise_for_status()
    raise RuntimeError("tfl request failed")
    # TODO: if request failed, do not draw map

def _bulk_station_distruptions(ids, chunk=20):
    output = []
    for i in range(0, len(ids), chunk):
        batch = ids[i:i + chunk] #slice i up to but not including i + chunk. ~30 calls
        r = _call(cfg.STATIONS_BULK_EP, stationId=",".join(batch))
        output.extend(r.json())
    cfg.logger.info(output)
    return output

def line_statuses():
    """ return general line statuses """
    r = _call(cfg.LINE_STATUS_EP)
    return r.json()

def station_statuses():
    """ return status and distruption data of all stations """
    return _bulk_station_distruptions(cfg.station_ids)
