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
        self._stop = threading.Event()
        self._dirty = True

        self.object = {} #([name] = [xpos, ypos, sprite])
        self._station_keys = {} # station key index (seto'objectnames)

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

        if w < 2 or h < 2:
            return #refuse service
        
        inner_w = w - 2
        inner_h = h - 2

        if inner_w <= 0 or inner_h <= 0:
            return 
        
        items = [] 
        for i in range(w):
            # example: 1002018:t:4 = [(5+4),6, "─" ]
            # 1002018:b:4 = [(5+4),(6+3 - 1), "─" ] (last row)
            items.append((f"{station_id_ics}:t:{i}", xpos + i, ypos, "─"))
            items.append((f"{station_id_ics}:b:{i}", xpos + i, ypos + h - 1, "─"))
        
        for j in range(h):
            items.append((f"{station_id_ics}:l:{j}", xpos, ypos+ j, "│"))
            items.append((f"{station_id_ics}:r:{j}", xpos + w - 1, ypos + j, "│"))
        items += [ # learnt this trick from a plumber
            (f"{station_id_ics}:tl", xpos, ypos, "┌"),
            (f"{station_id_ics}:tr", xpos + w - 1, ypos, "┐"),
            (f"{station_id_ics}:bl", xpos, ypos + h - 1, "└"),
            (f"{station_id_ics}:br", xpos + w - 1, ypos + h - 1, "┘")
        ]
        station_text = []
        if title and len(title) <= inner_w:
            station_text.append(title)
        station_text.extend(rows)

        wrappedt = []
        for line in station_text:
            wrappedt.extend(self._wrap(line, inner_w))
        for row, line in enumerate(wrappedt[:inner_h]):
            for col, ch in enumerate(line[:inner_w]):
                items.append((
                    f"{station_id_ics}:txt:{row}:{col}",
                    xpos + 1 + col, ypos + 1 + row, ch 
                ))

        with self._lock:
            old = self._station_keys.pop(station_id_ics, None)
            if old:
                for o in old:
                    self.object.pop(o, None)

            new_keys = set()
            obj = self.object
            for name, ox, oy, ch in items: # objectxm,objecty, character
                obj[name] = [ox, oy, ch]
                new_keys.add(name)
            self._station_keys[station_id_ics] = new_keys
            self._dirty = True

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
        
        # reuse grid and clea via slice assign
        with self._lock:
            if not self._dirty:
                return
            self._dirty = False
            cam_x, cam_y = self.cam_xpos, self.cam_ypos
            objects = list(self.object.values())

            grid = self._grid
            cols = self._cols
            rowns_n = self._rows
            
            for row in grid:
                row[:] = self._blank_row
                # copied template list contents (no per row allocation)

            # add thingys
            for xpos, ypos, sprite in objects:
                sx = xpos - cam_x
                sy = ypos - cam_y
                # sx/sy = screen xpos/screen ypos

                if 0 <= sx < cols  and 0 <= sy < rowns_n: 
                    grid[sy][sx] = sprite
                    # sxsy will allow the "camera" to move.
            
            top = "┼" + "─" * cols + "┼"
            #TODO: add little help module at bottom 
            # f"arrows to pan | {time.strftime("%H:%M:%S")}"
            ouptut = [top]
            for row in grid:
                ouptut.append("│" + "".join(row) + "│")
            ouptut.append(top)
            sys.stdout.write("\x1b[H"+ "\n".join(ouptut)) #ansi escape code
            sys.stdout.flush()

    def start(self):
        #check linjuxw/window
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write("\x1b[?25l") # hides cursor

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


# dummy data because i want to know it works  ˶ᵔᵕᵔ˶
ics_dummy_data_pls_delete_soon_thanks = {
    "1142069": {
        "stations": {
            "940GZZLUWLO": {
                "common_name": "I Forgot Station",
                "lines": ["bakerloo", "jubilee", "northern", "waterloo-city"],
                "modes": ["tube"],
                "status": "10",
                "desc": "hello i am a description and i am used to describe things about this topic",
            }
        }
    }
}
def start_map():
    murp = Map()
    murp.draw_ics_stations(ics_dummy_data_pls_delete_soon_thanks)
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

start_map()