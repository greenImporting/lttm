lttm can be split up into x amount of parts.

## UI
dirty flags and locks to prevent change during reads
### settings

- UPDOWNLEFTRIGHT+-

zoom

## application
hello ignore below

to update, we need to be able to refresh all data.
that means one thread running the map, then another thread
to get new info every minute, then a middleman to update map. dirty flag and separate thread locking already implemented in map for usage.

i think maybe at this current point i just want to be able to draw everything and get it to 'work'


everything will be updated at once, like a sweep of the board (think split-flap display?)
every 45-60s, queue mass update. iterate through all lines, get status of whole line, each station ( busy or not), and next stop 
once we have a 200 from all, refresh UI (who knows how ill implement the ui) by returning one big dictionary!


## config + extra fun
zoom of map (mayb), accent colors, map update, request rate, api keys??a

.env created on startup, user has to add key themselves for usage. will not support free plan because id otn want to


## api info for self. 
less data
