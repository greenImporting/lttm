import logging
from api import show_all_goodies
from bootstrap import check_files


logging.basicConfig( level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",)

logger = logging.getLogger(__name__)
logger.info("test")

if __name__ == "__main__":

    print(show_all_goodies())
    check_files()
    print("willkommen")