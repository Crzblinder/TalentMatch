import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.seed import seed_database
from app.models.base import Base, SessionLocal, engine


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name, "")
    if not value:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        fetch_real = _env_flag("FETCH_REAL_JOBS", default=True)
        result = seed_database(
            db,
            n_skills=80,
            n_companies=40,
            n_jobs=250,
            fetch_real=fetch_real,
        )
        print(f"Seeded: {result}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
