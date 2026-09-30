# refresh_data.py has been partially generated and modified with AI (deepseek)

the aim of refresh_data.py is to easily refresh all persistent data of the lines that can be found in data/

this hopefully won't need to be used unless there are changes/additions of stations on lines or the api changes.

forgive me for the ai usage but having it all in one big script saves time

(lowk i don't even know if it works)

## what are the files beginning with _ in data/ ?
_lines.json has all line metadata in one file.
_stations.json has all stations deduped across every line
_station_lines.json is reverse index, so input station id and get line

### fun ai generated example for usage
```
import json, pathlib
meow = pathlib.Path("data/")

lines    = json.loads((meow / "_lines.json").read_text())
stations = json.loads((meow / "_stations.json").read_text())
s2l      = json.loads((meow).read_text())

stations["910GEMRSPKH"]["common_name"]      # "Emerson Park Rail Station"
lines["weaver"]["station_order"]            # ordered station ids
s2l["910GEMRSPKH"]                          # ["liberty"]
```