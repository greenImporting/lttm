"""
communicates and filters with apis to recieve
each station/line data, then exposes through 
an all line status func. for another file to 
deal with it 🤣!!!!
"""
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

DP = Path("data/") # datapath

load_dotenv()

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
status_EP = f"{BASE}Line/Mode/{modes}/Status"
distruption_EP = f"{BASE}/StopPoint/{{stationId}}/Disruption"
# notes: status of whole line and each station within line. mass api + update

def current_key():
    return KEYS[_key_idx]

def switch_keys():
    global _key_idx
    _key_idx = (_key_idx + 1) % len(KEYS) # even=prim, odd=sec

def call(endpoint, **params): # w key value pairs (just learnt about them)
    url = endpoint.format(**params) 
    r = requests.get(url, params={"app_key": current_key()})
    if r.status_code == 429:
        swap_key()
        r = requests.get(url, params={"app_key": current_key()})
    return r 

def group_call(endpoint, ids, id_name):
    responses = {}
    for i in ids:
        meow = call(endpoint, **{id_name: i})
        responses[i] = meow.json()
    return

#TODO: check for 429 codes, switch to sec. key if applicable. 
# do not let user use without api key. bother until change
# (can be used without but i dont wanna :( )


def show_all_goodies():

    r = call("line", "status", lineId="windrush")
    print(r.json())
    print("done")

show_all_goodies()
print("doendone")