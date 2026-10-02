import logging
from api import show_all_goodies
from bootstrap import check_files


logging.basicConfig( level=logging.WARNING,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",)

log = logging.getLogger(__name__)


if __name__ == "__main__":

    show_all_goodies()
    check_files()
    print("willkommen")