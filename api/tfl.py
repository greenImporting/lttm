"""
communicates and filters with apis to recieve
each station/line data, then exposes through 
an all line status func. for another file to 
deal with it 🤣!!!!
"""
import os
import requests
from dotenv import load_dotenv

PRIM_KEY = os.getenv("PRIMARY_API_KEY")
SECOND_KEY = os.getenv("SECONDARY_API_KEY")
BASE = "https://api.tfl.gov.uk"

endpoints = {
    "line": {
        "route_sequence_inbound":  f"{BASE}/Line/{{lineId}}/Route/Sequence/inbound",
        "route_sequence_outbound": f"{BASE}/Line/{{lineId}}/Route/Sequence/outbound",
        "stop_points":             f"{BASE}/Line/{{lineId}}/StopPoints",
        "arrivals":                f"{BASE}/Line/{{lineId}}/Arrivals/{{stationId}}",
        "timetable":               f"{BASE}/Line/{{lineId}}/Timetable/{{fromStationId}}/to/{{toStationId}}",
    },
    "stoppoint": {
        "by_id":                   f"{BASE}/StopPoint/{{stationId}}",
        "arrivals":                f"{BASE}/StopPoint/{{stationId}}/Arrivals",
    },
}


def call(group, name, **params):
    url = endpoints[group][name].format(**params)
    return requests.get(url, params={"app_key": PRIM_KEY})


#TODO: make sure to check for codes. 429 is too many requests.
# if no api key: throw warning that youre rate limited, recommended to get api key
# if api key: check other key. if works: continue, if doesnt: wait 30s and try both keys again
# dont switch between if one works.

def show_all_goodies():
    load_dotenv()

    print("done")

show_all_goodies()
r = call("meta", "severity")
print(r.json())
print("doendone")