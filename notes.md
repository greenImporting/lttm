lttm can be split up into x amount of parts.

## UI
dirty flags and locks to prevent change during reads
### settings

- UPDOWNLEFTRIGHT+-

zoom

## application
~~grab info from apis about lines and stations~~
^ grab status updates about lines and stations from api. persistent data already set up.
filter and format data, exposes func. for map to use, draw and update

there are 3 parts that are necessary ( and are updated )
status of line (general overview, i think nice to have)
status of each station
~~status of next stop of each train on each line.~~ to be handled later. calling in chunks of 20 + built in compression by browsers should use less bandw. potential stickings



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
