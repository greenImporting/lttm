import sys
import shutil
import os
import time
import readchar
import threading
import queue

#NOTE: ics_code to be used to draw stations, then fetch all stations/lines relating
# to that ics code for expanded tooltips.

class Map:
    def __init__(self):
        tsize = shutil.get_terminal_size(fallback=(80,30)) #
        self.w = tsize.columns
        self.h = tsize.lines

        self.object = {} #([name] = [xpos, ypos, sprite])

        self.cam_xpos = 0
        self.cam_ypos = 0

    def add_object(self, name , xpos, ypos, charactr: str):
        self.object[name] = [xpos,ypos,charactr]
    
    def eviscerate_object(self, name):
        self.object.pop(name, None)

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

        if inner_w <=0 or inner_h <= 0:
            return 
        
        for i in range(w):
            # example: 1002018:t:4 = [(5+4),6, "─" ]
            # 1002018:b:4 = [(5+4),(6+3 - 1), "─" ] (last row)
            self.add_object(f"{station_id_ics}:t:{i}", xpos+i, ypos, "─")
            self.add_object(f"{station_id_ics}:t:{i}", xpos+i, ypos + h - 1, "─")
        
        for j in range(h):
            self.add_object(f"{station_id_ics}:t:{i}", xpos, ypos+ j, "│")
            self.add_object(f"{station_id_ics}:t:{i}", xpos+w - 1, ypos + j, "│")

        self.add_thing(f"{station_id_ics}:tl", xpos, ypos, "┌")
        self.add_thing(f"{station_id_ics}:tr", xpos + w - 1, ypos, "┐")
        self.add_thing(f"{station_id_ics}:bl", xpos, ypos + h - 1, "└")
        self.add_thing(f"{station_id_ics}:br", xpos + w - 1, ypos + h - 1, "┘")

        station_text = []
        if title and len(title) <= inner_w:
            station_text.append(title)
        text.extend(rows)

        # text truncation. assisted here
        # note4self, [:inner_h] takes only what you can handle (stop at inner height)
        for row, line in enumerate(station_text[:inner_h]):
            truncd = str(line)[:inner_w]
            for col, ch in enumerate(truncd):
                self.add_object(
                    f"{station_id_ics}:txt:{row}:{col}",
                    xpos + 1 + col, ypos + 1 + row, ch 
                )

    def draw_ics_stations(self):
        # params: ics data, top left x and y, box dimensions, padding?
        #loop over data, append data to some rows thjen build w/ 
        # draw station
        return
    
    def move_cam(self, dx, dy):
        self.cam_xpos += dx
        self.cam_ypos += dy
    
    def render_map(self):
        # im all for one liners but i prefer readability sometimes
        grid = []
        for _ in range(self.h - 2):
            # -2 for borders
            grid.append([' '] * (self.w - 2))
        
        # add thingys
        for xpos, ypos, thing in self.object.values():
            sx = xpos - self.cam_xpos
            sy = ypos - self.cam_ypos
            # sx/sy = screen xpos/screen ypos

            if 0 <= sx < self.w -2 and 0 <= sy < self.h - 2: 
                grid[sy][sx] = thing
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

# lveolyt test box to show that it works 
murp.add_object("squareT", 10, 9, "─" )
murp.add_object("squareTL", 9, 9, "┌" )
murp.add_object("squareTR", 11, 9, "┐" )


murp.add_object("squareB", 10, 10, "─" )
murp.add_object("squareBL", 9, 10, "└" )
murp.add_object("squareBR", 11, 10, "┘" )


murp.start()
try:
    while True:
        try:
            keyi = murp._keys.get(timeout=0.5) 
        except queue.Empty:
            keyi = None

        # l x-=1, r x+=1, u y-=1, d y+=1
        if keyi == readchar.key.UP:
            murp.move_cam(0, -1)
        elif keyi == readchar.key.DOWN:
            murp.move_cam(0, 1)
        elif keyi == readchar.key.LEFT:
            murp.move_cam(-1, 0)
        elif keyi == readchar.key.RIGHT:
            murp.move_cam(1, 0)

        murp.render_map()
        time.sleep(0.1) #TODO: dirty flag (refrender only when needed)
finally:
    murp.stop()

