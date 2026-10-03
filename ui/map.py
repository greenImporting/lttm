import sys
import shutil
import os
import time

class Map:
    def __init__(self):
        tsize = shutil.get_terminal_size(fallback=(80,30)) #
        self.w = tsize.columns
        self.h = tsize.lines
    
    def render_map(self):
        # im all for one liners but i prefer readability sometimes
        grid = []
        for _ in range(self.h - 2):
            # -2 for borders
            grid.append([' '] * (self.w - 2))
        
        top = "┼" + "─" * (self.w - 2) + "┼"
        rows = []
        for row in grid:
            rows.append("│" + "".join(row) + "│")
        map_l = [top] + rows + [top] # stackl em
        sys.stdout.write("\x1b[H"+ "\n".join(map_l)) #ansi escape code
        sys.stdout.flush()

    def start(self):
        #check linjuxw/window
        os.system('cls' if os.name== 'nt' else 'clear')
        sys.stdout.write("\x1b[?25l") # heard throught he grape vine that this hides the cursor
    
    def stop(self):
        sys.stdout.write("\x1b[?25h\n")# shows cursor

murp = Map()
murp.start()
try:
    while True:
        murp.render_map()
        time.sleep(1)
finally:
    murp.stop()

