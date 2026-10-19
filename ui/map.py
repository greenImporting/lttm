import sys
import shutil
import os
import time
import readchar
import threading
import queue
import math
import logging
from dataclasses import dataclass

#TODO LIST:
# - actually just fix formatting overall
#   ^ 3+ stations break it, formatting for station names is TERRIBLE!!
# - test and measure performance for large amount of objects
# - zooming logic (1 -> 16x~ only)
logger = logging.getLogger(__name__)

@dataclass
# note4self:
# @dataclass is a decorator that auto generates init, repr and eq from calss level type
# annotated attributes.
# learnt this trick from a plumber
class Station:
    x: int
    y: int
    w: int
    h: int
    station_sprite: list[list[str]]
class Map:
    def __init__(self):
        tsize = shutil.get_terminal_size(fallback=(80,30))
        self.w = tsize.columns
        self.h = tsize.lines

        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._dirty = True

        self.stations = {} #station_id-> Station

        self.cam_xpos = 0
        self.cam_ypos = 0

        # preallocating render buffers
        # when resize logic comes round ( later icba now,)
        # reallocate grid, blank row, col rows etc inside render_map when 
        # shutils terminal size changes 
        self._cols = self.w - 2
        self._rows = self.h - 2
        self._grid = [[''] * self._cols for _ in range(self._rows)]
        self._blank_row = [' '] * self._cols


    def _wrap(self, text: str, width):
        # wrap text where text needs wrapped. assisted here

        if width <= 0:
            return []
        
        words = str(text).split()

        if not words:
            return [""]
        
        current = ""
        lines = []

        for word in words:
            if not current:
                while len(word) > width:
                    #lines.append(word[:width])
                    lines.append(word[width:])
                    word = word[width:]
                current = word
            elif len(current) + 1 + len(word) <= width:
                current += " " + word
            else:
                lines.append(current)
                while len(word) > width:
                    lines.append(word[width:])
                    word = word[width:]
                current = word
        if current:
            lines.append(current)
        return lines

    def _compute_geo_bounds(self, ics_data):
        lats, lons = [], []
        for entry in ics_data.values():
            for stn in entry["stations"].values():
                lat, lon = stn.get("lat"), stn.get("lon")
                if lat is None or lon is None:
                    continue
                lats.append(lat)
                lons.append(lon)
        if not lats:
            # no lats = no lons aswel
            logger.warn(f"returning default vAlues")
            return 0.0,1.0,0.0,1.0 
        return min(lats), max(lats), min(lons), max(lons)


    def _project(self, lat,lon, bounds, cols, rows):
        lat_min, lat_max, lon_min, lon_max = bounds
        lon_span = lon_max- lon_min
        lat_span = lat_max - lat_min
        x = (lon - lon_min) / lon_span * cols if lon_span else cols / 2
        y = (lat_max - lat) / lat_span * rows if lat_span else rows / 2

        #guard against zero span bounds
        return int(x), int(y * 0.5) # terminal makes it funky when not *0.5

    def _ics_centroids(self, ics_data):
        # means the lat and lon of each ics station (average centre if multiple staions)
        out = {}
        for ics, entry in ics_data.items():
            stations = list(entry["stations"].values())
            out[ics] = (
                sum(stn["lat"] for stn in stations) / len(stations),
                sum(stn["lon"] for stn in stations) / len(stations)
            )
        return out
    def build_station(self, w, h, title="", rows=None):
        rows = rows or []

        if w < 2 or h < 2:
            return #refuse service
        
        inner_w = w - 2
        inner_h = h - 2

        if inner_w <= 0 or inner_h <= 0:
            return
        
        station_sprite = [[" "] * w for _ in range(h)]
        for i in range(w):
            station_sprite[0][i] = "─"
            station_sprite[h-1][i] = "─"
        for j in range(h):
            station_sprite[j][0] = "│"
            station_sprite[j][w-1] = "│"
        
        station_sprite[0][0] = "┌"
        station_sprite[0][w - 1] = "┐"
        station_sprite[h - 1][0] = "└"
        station_sprite[h - 1][w - 1] = "┘"

        station_text = []
        if title:
            station_text.append(title)
        station_text.extend(rows)
        
        wrappedt = []
        for line in station_text:
            wrappedt.extend(self._wrap(line, inner_w))

        for row, line in enumerate(wrappedt[:inner_h]):
            for col, ch in enumerate(line[:inner_w]):
                station_sprite[row + 1][col + 1] = ch #+1 to skip bordr

        return station_sprite

    def draw_station(self, station_id_ics, xpos, ypos, w, h, title="", rows=None):

        station_sprite = self.build_station(w, h, title, rows)
        if station_sprite is None:
            return

        with self._lock:
            self.stations[station_id_ics] = Station(xpos,ypos,w,h,station_sprite)
            self._dirty = True

    def draw_ics_stations(self, ics_data, tlx=1, tly=1, station_w=40, station_h=12, padding=1):
        cols = self.w - 2
        rows = (self.h -2) * 2 # * 2 bc y was halved
        bounds = self._compute_geo_bounds(ics_data)
        centroids = self._ics_centroids(ics_data)

        for ics, (lat,lon) in centroids.items():
            cx,cy = self._project(lat,lon,bounds, cols, rows) #centre x and y
            # now anchor box at its centre
            x = cx - station_w // 2
            y = cy - station_h // 2
            
            stn_rows = []
            ics_entry = ics_data[ics]
            stations_dict = ics_entry["stations"]
            stations_list = list(stations_dict.values())
            if not stations_list:
                continue #nextiteration


            title = stations_list[0].get("common_name", "")

            for stati in stations_list:
                if len(stations_list) > 1:
                    stn_rows.append(stati.get("common_name", "")) # can switch to using lookup table for common names (less reliance)
                stn_rows.append("lines: "+ ", ".join(stati.get("lines", [])))
                stn_rows.append("modes: "+", ".join(stati.get("modes", [])))
                stn_rows.append("status: " + stati.get("status", "?")) # placeholder for now. awaiting real data from api
                stn_rows.append("desc: " + stati.get("desc", "?"))
            
            self.draw_station(ics, x, y, station_w, station_h, title, stn_rows)

    
    def render_map(self):
        
        # reuse grid and clea via slice assign
        with self._lock:
            if not self._dirty:
                return
            self._dirty = False
            cam_x, cam_y = self.cam_xpos, self.cam_ypos
            stations = list(self.stations.values())

            grid = self._grid
            cols = self._cols
            rowns_n = self._rows
            
            for row in grid:
                row[:] = self._blank_row
                # copied template list contents (no per row allocation)

            for station in stations:
                sx = station.x - cam_x
                sy = station.y - cam_y
                # sx/sy = screen xpos/screen ypos

                if sx >= cols or sy >= rowns_n or sx+station.w <= 0 or sy + station.h <= 0:
                    continue # cull if fully off screen
            
                x0 = max(0,-sx)
                y0 = max(0,-sy)
                x1 = min(station.w, cols - sx)
                y1 = min(station.h, rowns_n - sy)

                for row_y in range(y0, y1): #walk visible rows of sspirets
                    grid_y = sy + row_y
                    row = station.station_sprite[row_y]
                    for row_x in range(x0,x1):
                        grid[grid_y][sx+ row_x] = row[row_x] # screen col, rx = sprite col

            top = "┼" + "─" * cols + "┼"
            #TODO: add little help module at bottom 
            # f"arrows to pan | {time.strftime("%H:%M:%S")}"
            ouptut = [top]
            for row in grid:
                ouptut.append("│" + "".join(row) + "│")
            ouptut.append(top)
            sys.stdout.write("\x1b[H"+ "\n".join(ouptut)) #ansi escape code
            sys.stdout.flush()

    def move_cam(self, dx, dy):
        with self._lock:
            self.cam_xpos += dx
            self.cam_ypos += dy
            self._dirty = True

    
    def start(self):
        #check linjuxw/window
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write("\x1b[?25l") # hides cursor

        self._keys = queue.Queue() #Q4KEYS
        self._thread = threading.Thread(target=self._listen, args=(self._keys, self._stop), daemon=True)
        self._thread.start()

    def update_station(self, station_id, xpos, ypos, w, h, title="", rows=None):
        station_sprite = self.build_station(w,h,title,rows)
        if station_sprite is None:
            return
        with self._lock:
            self.stations[station_id] = Station(xpos,ypos,w,h,station_sprite)
            self._dirty = True
        

    def _listen(self, q, stop):
        while not stop.is_set():
            key = readchar.readkey()
            if key in (
                readchar.key.UP,
                readchar.key.DOWN,
                readchar.key.LEFT,
                readchar.key.RIGHT,
            ):
                q.put(key)
            elif key.lower() == "q":
                stop.set()
                q.put("q")

    def stop(self):
        self._stop.set()
        sys.stdout.write("\x1b[H")
        sys.stdout.write("\x1b[?25h\n")# shows cursor


def start_map(ics_station_statuses, line_statuses):
    murp = Map()
    murp.draw_ics_stations(ics_station_statuses)
    murp.start()
    try:
    # caches all but queue to gaurantee murp stops
        while not murp._stop.is_set():
        # main loop that runs forevre till interruption 
            try:
                while True:
                # drains every pending key ( no more backlog)
                    keyi = murp._keys.get_nowait()
                    if keyi == "q":
                        murp._stop.set()
                        break
                    if keyi == readchar.key.UP:
                        murp.move_cam(0, -1)
                    elif keyi == readchar.key.DOWN:
                        murp.move_cam(0, 1)
                    elif keyi == readchar.key.LEFT:
                        murp.move_cam(-1, 0)
                    elif keyi == readchar.key.RIGHT:
                        murp.move_cam(1, 0)
            except queue.Empty:
                pass

            murp.render_map()
            time.sleep(0.05)
    finally:
        murp.stop()
