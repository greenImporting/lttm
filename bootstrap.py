"""
this module will check if necessary files exist,
and if not, create them!
"""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent
# files will have tuples of file, data. so if file doesnt exist, touch and cp data
files = [
    (root / ".env", root / ".env.example"),
]


def check_files():
    """checks if necessary files exist, touch and fill if not"""
    for file, template in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        if not file.exists():
            shutil.copy(template,file)
    print("files checked")

