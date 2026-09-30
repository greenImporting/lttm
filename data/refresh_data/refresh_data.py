import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

prim_key = os.getenv("PRIMARY_API_KEY")
base = "https://api.tfl.gov.uk"
here = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(here, "data")

whitelist = {
    "line_id", "line_name", "lineId", "lineName", "direction", "isOutboundOnly", "mode",
    "lineStrings", "stations", "stopPointSequences", "orderedLineRoutes", "stop_points", "stoppoints",
    "id", "name", "lat", "lon", "naptanId", "commonName", "icsId", "icsCode", "modes", "lines",
    "branchId", "nextBranchIds", "prevBranchIds", "stopPoint", "serviceType",
    "naptanIds"
}

def get(url):
    params = {"app_key": prim_key} if prim_key else {}
    return requests.get(url, params=params)

def filter_data(data):
    if isinstance(data, dict):
        return {k: filter_data(v) for k, v in data.items() if k in whitelist}
    if isinstance(data, list):
        return [filter_data(item) for item in data]
    return data

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def line_ids():
    if not os.path.isdir(data_dir):
        print("missing data dir:", data_dir)
        return []

    skip = {"lines", "stoppoints"}
    ids = [
        os.path.splitext(fn)[0]
        for fn in os.listdir(data_dir)
        if fn.endswith(".json")
        and not fn.startswith("filtered_")
        and os.path.splitext(fn)[0] not in skip
    ]
    return sorted(set(ids))

def collect_line(lid, stations):
    out = {}
    urls = {
        "route_sequence_inbound": f"{base}/Line/{lid}/Route/Sequence/inbound",
        "route_sequence_outbound": f"{base}/Line/{lid}/Route/Sequence/outbound",
        "stop_points": f"{base}/Line/{lid}/StopPoints",
    }

    for name, url in urls.items():
        r = get(url)
        print(lid, name, r.status_code)

        if not r.ok:
            out[name] = {"status": r.status_code}
            continue

        data = r.json()
        out[name] = data

        if isinstance(data, dict):
            for seq in data.get("stopPointSequences", []) or []:
                for sp in seq.get("stopPoint", []) or []:
                    if sp.get("id"):
                        stations.add(sp["id"])
            for sp in data.get("stopPoints", []) or []:
                if sp.get("id"):
                    stations.add(sp["id"])
        elif isinstance(data, list):
            for sp in data:
                if isinstance(sp, dict) and sp.get("id"):
                    stations.add(sp["id"])

    return out

def filter_all_json_files():
    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue
        if filename.startswith("filtered_"):
            continue

        filepath = os.path.join(data_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        filtered = filter_data(data)
        outpath = os.path.join(data_dir, f"filtered_{filename}")
        write_json(outpath, filtered)
        print(f"processed {filepath} -> {outpath}")

def main():
    os.makedirs(data_dir, exist_ok=True)

    ids = line_ids()
    print("line ids:", ids)

    stations = set()
    lines = {}

    for lid in ids:
        lines[lid] = collect_line(lid, stations)

    write_json(os.path.join(data_dir, "lines.json"), lines)

    stops = {}
    for sid in sorted(stations):
        r = get(f"{base}/StopPoint/{sid}")
        print("stop", sid, r.status_code)
        stops[sid] = r.json() if r.ok else {"status": r.status_code}

    write_json(os.path.join(data_dir, "stoppoints.json"), stops)

    filter_all_json_files()

    print("done", len(ids), "lines", len(stops), "stops")

if __name__ == "__main__":
    main()