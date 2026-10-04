lttm can be split up into x amount of parts.

## UI
threading ui using readchar to await arrow skyes to move map.
very simple map, maybe initially not accurate to london, maybe in future we add movement across an underground0styled map.

key listener probably will be a daemon thread that puts events into a queue
for main to deal w/.
arrow keys only for now, maybe more keybinds later for settings etc.

### settings

- UPDOWNLEFTRIGHT+-

hihglight stations?

please dont make me zoom.

## application
~~grab info from apis about lines and stations~~
^ grab status updates about lines and stations from api. persistent data already set up.
filter and format data,  store for calling later
 send important info off to front end ( status changes of places.)

there are x amount of parts that are necessary ( and are updated )
status of line (general overview, i think nice to have)
status of each station
~~status of next stop of each train on each line.~~ issue with this is that the best way i can get all prediction data is call api every 1-5 mins that gives me a file of 10mb. how is this viable??? 



lets first just station, map and status updates.

will most likely work like this:
everything will be updated at once, like a sweep of the board (think split-flap display?)
every 45-60s, queue mass update. iterate through all lines, get status of whole line, each station ( busy or not), and next stop 
once we have a 200 from all, refresh UI (who knows how ill implement the ui) by returning one big dictionary!


## config + extra fun
zoom of map (mayb), accent colors, map update, request rate, api keys??a

.env created on startup, user has to add key themselves for usage. will not support free plan because id otn want to


## api info for self. 
less data
