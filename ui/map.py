import sys
import shutil
import os
import time
import readchar
import threading
import queue



class Map:
    def __init__(self):
        tsize = shutil.get_terminal_size(fallback=(80,30)) #
        self.w = tsize.columns
        self.h = tsize.lines

        self.testobject = {} #([name] = [xpos, ypos, sprite])
        self.cam_xpos = 0
        self.cam_ypos = 0

    def add_thing(self, name , xpos, ypos, thing: str):
        self.testobject[name] = [xpos,ypos,thing]
    
    def eviscerate_thing(self, name):
        self.testobject.pop(name, None)
    
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
        for xpos, ypos, thing in self.testobject.values():
            sx = xpos - self.cam_xpos
            sy = ypos - self.cam_ypos
            # sx/sy = screen xpos/screen ypos

            if 0 <= sx < self.w -2 and 0 <= sy < self.h - 2: 
                grid[sy][sx] = thing
                # sxsy will allow the "camera" to move.
        
        top = "┼" + "─" * (self.w - 2) + "┼"
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
murp.add_thing("squareT", 10, 9, "─" )
murp.add_thing("squareTL", 9, 9, "┌" )
murp.add_thing("squareTR", 11, 9, "┐" )


murp.add_thing("squareB", 10, 10, "─" )
murp.add_thing("squareBL", 9, 10, "└" )
murp.add_thing("squareBR", 11, 10, "┘" )


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

