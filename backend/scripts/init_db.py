import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.init_db import init_db


def main():
    init_db(seed=True, rebuild_vector_store=False)


if __name__ == "__main__":
    main()
