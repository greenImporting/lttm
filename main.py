import logging
from api import get_station_formatted_ics,clean_line_statuses, station_statuses, line_statuses
from bootstrap import check_files
from ui import start_map

file_handler = logging.FileHandler("app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))

logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler())

logger.info("Welcome!")

# initial start up ---
# get status data for lines and stations
# clean that data
# pass that data into start map
# ---
# regular workings after that ---
# separate thread waits every 60 seconds, then grabs statuses for lines and stations
# feed into an update_map() function
# map will refresh with new data
# ---

def first_run():
    cleaned_line_info = clean_line_statuses(line_statuses())
    print("cleaned line info recieved")
    cleaned_station_info = get_station_formatted_ics(station_statuses())
    print("cleaned station info recieved")
    start_map(cleaned_station_info, cleaned_line_info)

if __name__ == "__main__":
    first_run()
