""" usage:
- clean_line_statuses(data) - clean line status api data
- get_station_formatted_ics(data) - format station status data (for map)"""
from . import config as cfg

def clean_line_statuses(data):
    """get first status of each line"""
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        # got told this is good practise to do

        statuses = item.get("lineStatuses") or []
        status = statuses[0] if statuses and isinstance(statuses[0], dict) else {}
        result.append({
            "id": item.get("id"),
            "statusSeverity": status.get("statusSeverity"),
            "statusSeverityDescription": status.get("statusSeverityDescription"),
        })
    return result

def clean_station_statuses(data):
    """get first status of each station"""
    result = []
    for item in data:
        if not isinstance(item, dict):
            cfg.logger.warning(f"{item} is not a dict")
            continue

        result.append({
                "id": item.get("stationAtcoCode") or item.get("atcoCode"),
                "statusSeverity": item.get("type"),
                "statusSeverityDescription": item.get("description"),
            })
    return result



def format_to_ics(cleaned_station_data):
    """
    group cleaned statsion data by ics code
    """
    outputer = {}
    for station in cleaned_station_data or []: # ^^
        station_id = station.get("id")
        current_station = cfg.stations.get(station_id)

        if not current_station:
            continue

        ics_code = current_station.get("ics_code")
        if not ics_code:
            continue

        outputer.setdefault(ics_code, {"stations": {}}) 
        cfg.logger.info(f"{station}'s current_station={current_station}, ics_code={ics_code}")
        outputer[ics_code]["stations"][station_id] = {
            "common_name": current_station.get("common_name"),
            "lat": current_station.get("lat"),
            "lon": current_station.get("lon"),
            "lines": [line.get("id") for line in current_station.get("lines", [])],
            "modes": current_station.get("modes", []),
            "status": station.get("statusSeverity"),
            "desc": station.get("statusSeverityDescription")
        }
    return outputer

def get_station_formatted_ics(data):
    return format_to_ics(clean_station_statuses(data))
