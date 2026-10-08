import sys
import shutil
import os
import time
import readchar
import threading
import queue

#TODO LIST:
# - actually just fix formatting overall
# - assume that all hell breaks loose once one too many things are in objects. must plan ahead
# - zoom in zoom out features dude :/ . imagine trying to get from left to right of london with a station the the width of 30chars
# - update maps according to object names
# - fix quitting (shouldnt have to ctrl c twice )
class Map:
    def __init__(self):
        tsize = shutil.get_terminal_size(fallback=(80,30)) #
        self.w = tsize.columns
        self.h = tsize.lines

        self._lock = threading.Lock()
        self._dirty = True

        self.object = {} #([name] = [xpos, ypos, sprite])
        # i wonder if i could cull these?

        self.cam_xpos = 0
        self.cam_ypos = 0

    def add_object(self, name , xpos, ypos, charactr: str):
        with self._lock:
            self.object[name] = [xpos,ypos,charactr]
            self._dirty = True 

    def eviscerate_object(self, name):
        with self._lock:
            self.object.pop(name, None)
            self._dirty = True

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
                    lines.append(word[:width])
                    word = word[:width]
                current = word
            elif len(current) + 1 + len(word) <= width:
                current += " " + word
            else:
                lines.append(current)
                while len(word) > width:
                    lines.append(word[:width])
                    word = word[:width]
                current = word
        if current:
            lines.append(current)
        return lines

    def draw_station(self, station_id_ics, xpos, ypos, w, h, title="", rows=None):
        rows = rows or []

        # clean previosuly drawn cells 
        for obj in list(self.object):
            if obj.startswith(station_id_ics+ ":"):
                self.eviscerate_object(obj)

        if w < 2 or h < 2:
            return #refuse service
        
        inner_w = w - 2
        inner_h = h - 2

        if inner_w <= 0 or inner_h <= 0:
            return 
        
        for i in range(w):
            # example: 1002018:t:4 = [(5+4),6, "─" ]
            # 1002018:b:4 = [(5+4),(6+3 - 1), "─" ] (last row)
            self.add_object(f"{station_id_ics}:t:{i}", xpos + i, ypos, "─")
            self.add_object(f"{station_id_ics}:b:{i}", xpos + i, ypos + h - 1, "─")
        
        for j in range(h):
            self.add_object(f"{station_id_ics}:l:{j}", xpos, ypos+ j, "│")
            self.add_object(f"{station_id_ics}:r:{j}", xpos + w - 1, ypos + j, "│")

        self.add_object(f"{station_id_ics}:tl", xpos, ypos, "┌")
        self.add_object(f"{station_id_ics}:tr", xpos + w - 1, ypos, "┐")
        self.add_object(f"{station_id_ics}:bl", xpos, ypos + h - 1, "└")
        self.add_object(f"{station_id_ics}:br", xpos + w - 1, ypos + h - 1, "┘")

        station_text = []
        if title and len(title) <= inner_w:
            station_text.append(title)
        station_text.extend(rows)

        wrappedt = []
        for line in station_text:
            wrappedt.extend(self._wrap(line, inner_w))
        for row, line in enumerate(wrappedt[:inner_h]):
            for col, ch in enumerate(line[:inner_w]):
                self.add_object(
                    f"{station_id_ics}:txt:{row}:{col}",
                    xpos + 1 + col, ypos + 1 + row, ch 
                )

    def draw_ics_stations(self, ics_data, tlx=1, tly=1, station_w=40, station_h=12, padding=1):
        # tl* = top left x/y, such as x0 or y0
        x, y = tlx, tly
        for ics, entry in ics_data.items():
            rows = []
            stations = entry.get("stations", {})
            first_station = next(iter(stations.values()), {}) #iterate over first stations
            title = entry.get("name") or first_station.get("common_name", "")
            for station_id, stati in entry.get("stations", {}).items():
                if len(stations) > 1:
                    rows.append(stati.get("common_name", "")) # can switch to using lookup table for common names (less reliance)
                rows.append("lines: "+ ", ".join(stati.get("lines", [])))
                rows.append("modes: "+", ".join(stati.get("modes", [])))
                rows.append("status: " + stati.get("status", "?")) # placeholder for now. awaiting real data from api
                rows.append("desc: " + stati.get("desc", "?"))
            
            self.draw_station(ics, x, y, station_w, station_h, title, rows)

            x += station_w + padding
            if x + padding > self.w:
                x = tlx
                y += station_h + padding
    
    def move_cam(self, dx, dy):
        with self._lock:
            self.cam_xpos += dx
            self.cam_ypos += dy
            self._dirty = True

    
    def render_map(self):
        
        # mutated when updated, and iterated through by renderer
        # prevent runtimeerrors by setting inside
        with self._lock:
            if not self._dirty:
                return
            self._dirty = False
            cam_x, cam_y = self.cam_xpos, self.cam_ypos
            objects = list(self.object.values())

            grid = []
            for _ in range(self.h - 2):
                # -2 for borders
                grid.append([' '] * (self.w - 2))
            
            # add thingys
            for xpos, ypos, sprite in objects:
                sx = xpos - cam_x
                sy = ypos - cam_y
                # sx/sy = screen xpos/screen ypos

                if 0 <= sx < self.w -2 and 0 <= sy < self.h - 2: 
                    grid[sy][sx] = sprite
                    # sxsy will allow the "camera" to move.
            
            top = "┼" + "─" * (self.w - 2) + "┼"
            #TODO: add little help module at bottom 
            # f"arrows to pan | {time.strftime("%H:%M:%S")}"
            rows = []
            for row in grid:
                rows.append("│" + "".join(row) + "│")
            map_l = [top] + rows + [top] # stackl em
            sys.stdout.write("\x1b[H"+ "\n".join(map_l)) #ansi escape code
            sys.stdout.flush()

    def start(self):
        #check linjuxw/window
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write("\x1b[?25l") # hides cursor

        self._stop = threading.Event() #sharedflag
        self._keys = queue.Queue() #Q4KEYS
        self._thread = threading.Thread(target=self._listen, args=(self._keys, self._stop), daemon=True)
        self._thread.start()

    def _listen(self, q, stop):
        while not stop.is_set():
            key = readchar.readkey()
            if key in (
                readchar.key.UP,
                readchar.key.DOWN,
                readchar.key.LEFT,
                readchar.key.RIGHT
            ):
                q.put(key)
        
    def stop(self):
        self._stop.set()
        sys.stdout.write("\x1b[?25h\n")# shows cursor

murp = Map()

# dummy data because i want to know it works  ˶ᵔᵕᵔ˶
ics_dummy_data_pls_delete_soon_thanks = {
    "1142069": {
        "stations": {
            "940GZZLUWLO": {
                "common_name": "I Forgot Station",
                "lines": ["bakerloo", "jubilee", "northern", "waterloo-city"],
                "modes": ["tube"],
                "status": "probably",
                "desc": "hello i am a description and i am used to describe things about this topic",
            }
        }
    }
}

murp.draw_ics_stations(ics_dummy_data_pls_delete_soon_thanks)

murp.start()
try:
# caches all but queue to gaurantee murp stops
    while True:
    # main loop that runs forevre till interruption 
        try:
            while True:
            # drains every pending key ( no more backlog)
                keyi = murp._keys.get_nowait()
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

