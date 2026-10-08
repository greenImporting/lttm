""" usage:
line cleanup: call clean_statuses(data)
station cleanup & format ( for map ): get_station_formatted_ics(data)
"""
from . import config as cfg

def clean_statuses(data):
    result = []
    for d in data:
        result.append({
            "id": d.get("id"),
            "statusSeverity": (d.get("lineStatuses") or [{}])[0].get("statusSeverity"),
            "statusSeverityDescription": (d.get("lineStatuses") or [{}])[0].get("statusSeverityDescription"),
        })
    return result

def format_to_ics(cleaned_station_data):
    """
    get all cleaned station data (id,status,desc),
    get common name and ics code from cfg.stations,
    wrap up into a nice package
    """
    outputer = {}
    for station in cleaned_station_data:
        station_id = station.get("id")
        current_station = cfg.stations.get(station_id)

        if not current_station:
            continue

        ics_code = current_station.get("ics_code")
        #set ics as default cuz i wanna
        outputer.setdefault(ics_code, {"stations": {}}) 

        outputer[ics_code]["stations"][station_id] = {
            "common_name": current_station.get("common_name"),
            "lines": [line.get("id") for line in current_station.get("lines", [])],
            "modes": current_station.get("modes", []),
            "status": station.get("statusSeverity"),
            "desc": station.get("statusSeverityDescription")
        }
    return outputer

def get_station_formatted_ics(data):
    return format_to_ics(clean_statuses(data))