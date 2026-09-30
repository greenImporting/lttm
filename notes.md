lttm can be split up into x amount of parts.

## UI
draw map with curses (stdscr object will expose util)
very simple map, maybe initially not accurate to london, maybe in future we add movement across an underground0styled map.


## application
grab info from apis about lines and stations
filter and format data,  store for calling later
 send important info off to front end ( status changes of places.)

## config + extra fun
zoom of map (mayb), accent colors, map update, request rate, api keys??a


usage is limited to 50 without an api key, 500 with one. must write detailed how 2 2 make an account and get api key ( if you want to have this program be super duper useful to yourself), or use less per min

~5m for full refresh of data w/ no api key
~1m with api key

.gitignore has .env, user must use .env for app.