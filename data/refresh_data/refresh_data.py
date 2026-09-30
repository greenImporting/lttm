"""
please please read the README.md in refresh_data/ ,this will explain the sloppy ai usage

"""
import os
import json
import pathlib
import requests
from dotenv import load_dotenv

load_dotenv()

PRIMARY_API_KEY = os.getenv("PRIMARY_API_KEY")
BASE = "https://api.tfl.gov.uk"

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
RAW = DATA / "raw"
NORM = DATA / "normalized"

WHITELIST = {
    "line_id", "line_name", "lineId", "lineName", "direction", "isOutboundOnly", "mode",
    "lineStrings", "stations", "stopPointSequences", "orderedLineRoutes", "stop_points", "stoppoints",
    "id", "name", "lat", "lon", "naptanId", "commonName", "icsId", "icsCode", "modes", "lines",
    "branchId", "nextBranchIds", "prevBranchIds", "stopPoint", "serviceType",
    "naptanIds",
}


# ---------- fetch phase ----------

def get(url):
    params = {"app_key": PRIMARY_API_KEY} if PRIMARY_API_KEY else {}
    return requests.get(url, params=params)


def filter_data(data):
    if isinstance(data, dict):
        return {k: filter_data(v) for k, v in data.items() if k in WHITELIST}
    if isinstance(data, list):
        return [filter_data(i) for i in data]
    return data


def write_json(path, data):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def line_ids():
    if not RAW.is_dir():
        print("missing raw dir:", RAW)
        return []
    skip = {"lines", "stoppoints"}
    ids = [
        p.stem for p in RAW.iterdir()
        if p.suffix == ".json" and not p.name.startswith("filtered_") and p.stem not in skip
    ]
    return sorted(set(ids))


def collect_line(lid, stations):
    out = {}
    urls = {
        "route_sequence_inbound":  f"{BASE}/Line/{lid}/Route/Sequence/inbound",
        "route_sequence_outbound": f"{BASE}/Line/{lid}/Route/Sequence/outbound",
        "stop_points":             f"{BASE}/Line/{lid}/StopPoints",
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
    for p in RAW.iterdir():
        if p.suffix != ".json" or p.name.startswith("filtered_"):
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        filtered = filter_data(data)
        outpath = RAW / f"filtered_{p.name}"
        write_json(outpath, filtered)
        print(f"processed {p} -> {outpath}")


def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    ids = line_ids()
    print("line ids:", ids)

    stations = set()
    lines = {}
    for lid in ids:
        lines[lid] = collect_line(lid, stations)
    write_json(RAW / "lines.json", lines)

    stops = {}
    for sid in sorted(stations):
        r = get(f"{BASE}/StopPoint/{sid}")
        print("stop", sid, r.status_code)
        stops[sid] = r.json() if r.ok else {"status": r.status_code}
    write_json(RAW / "stoppoints.json", stops)

    filter_all_json_files()
    print("fetch done", len(ids), "lines", len(stops), "stops")


# ---------- normalise phase ----------

def pick_id(sp):
    return sp.get("naptanId") or sp.get("id")


def merge_station(existing, sp):
    existing["modes"] = sorted(set(existing["modes"]) | set(sp.get("modes", [])))
    known = {l["id"] for l in existing["lines"]}
    for l in sp.get("lines", []):
        if l.get("id") and l["id"] not in known:
            existing["lines"].append({"id": l["id"], "name": l.get("name", l["id"])})
            known.add(l["id"])
    existing["lines"].sort(key=lambda l: l["id"])


def normalize():
    NORM.mkdir(parents=True, exist_ok=True)

    stations = {}
    station_lines = {}
    lines_index = {}

    for path in sorted(RAW.glob("*.json")):
        if path.name.startswith("filtered_"):
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"skip {path.name}: invalid json")
            continue

        line_id = raw.get("line_id") or path.stem
        line_name = raw.get("line_name") or line_id
        sps = raw.get("stop_points") or raw.get("stoppoints") or []

        order = []
        for sp in sps:
            sid = pick_id(sp)
            if not sid:
                continue
            if sid not in stations:
                stations[sid] = {
                    "station_id": sid,
                    "naptan_id": sp.get("naptanId"),
                    "ics_code": sp.get("icsCode"),
                    "common_name": sp.get("commonName"),
                    "modes": sorted(sp.get("modes", [])),
                    "lines": sorted(
                        ({"id": l["id"], "name": l.get("name", l["id"])}
                         for l in sp.get("lines", []) if l.get("id")),
                        key=lambda l: l["id"],
                    ),
                    "lat": sp.get("lat"),
                    "lon": sp.get("lon"),
                }
            else:
                merge_station(stations[sid], sp)

            station_lines.setdefault(sid, [])
            if line_id not in station_lines[sid]:
                station_lines[sid].append(line_id)

            if sid not in order:
                order.append(sid)

        line_out = {
            "line_id": line_id,
            "line_name": line_name,
            "station_order": order,
            "stations": [stations[sid] for sid in order],
        }
        write_json(NORM / f"{line_id}.json", line_out)
        lines_index[line_id] = {
            "line_id": line_id,
            "line_name": line_name,
            "station_order": order,
        }

    write_json(NORM / "_lines.json", lines_index)
    write_json(NORM / "_stations.json", stations)
    write_json(NORM / "_station_lines.json", station_lines)

    print(f"normalize done lines={len(lines_index)} stations={len(stations)}")


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    fetch()
    normalize()


if __name__ == "__main__":
    main()