import logging
import os

from sqlalchemy import inspect
from sqlalchemy.sql import text

# 导入所有模型以注册到 Base.metadata
from app import models  # noqa: F401
from app.config import get_settings
from app.data.seed import seed_database
from app.models.base import Base, SessionLocal, engine
from app.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


def _ensure_columns(engine) -> None:
    """为已存在的数据表补齐模型新增的可空列，保证旧数据库能直接启动运行。"""
    inspector = inspect(engine)

    def _ensure_table_columns(table_name: str, columns: dict[str, str]) -> None:
        try:
            existing = {col["name"] for col in inspector.get_columns(table_name)}
        except Exception:
            return
        with engine.connect() as conn:
            for col_name, col_type in columns.items():
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
            conn.commit()

    _ensure_table_columns(
        "match_results",
        {
            "skill_score": "FLOAT",
            "experience_match": "FLOAT",
            "education_match": "FLOAT",
        },
    )
    _ensure_table_columns(
        "user_skill_profiles",
        {
            "is_active": "BOOLEAN DEFAULT 0",
        },
    )


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name, "")
    if not value:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def init_db(
    seed: bool = True,
    rebuild_vector_store: bool = True,
    fetch_real_jobs: bool | None = None,
) -> None:
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready.")

    if seed:
        if fetch_real_jobs is None:
            fetch_real_jobs = _env_flag("FETCH_REAL_JOBS", default=False)
        db = SessionLocal()
        try:
            result = seed_database(
                db,
                n_skills=80,
                n_companies=40,
                n_jobs=250,
                fetch_real=fetch_real_jobs,
            )
            logger.info("Seed result: %s", result)
        finally:
            db.close()

    if rebuild_vector_store:
        _rebuild_vector_store()


def _rebuild_vector_store() -> None:
    """Sync Job and Skill data from SQL database into Chroma vector store."""
    db = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload

        jobs = db.query(models.Job).options(joinedload(models.Job.company)).all()
        skills = db.query(models.Skill).all()
        if not jobs and not skills:
            logger.info("No jobs or skills found; skipping vector store rebuild.")
            return

        vector_store = get_vector_store()
        logger.info("Rebuilding vector store collection '%s'...", vector_store.collection_name)
        vector_store.clear_collection()

        indexed_jobs = vector_store.add_job_documents(jobs)
        indexed_skills = vector_store.add_skill_documents(skills)
        logger.info(
            "Vector store rebuilt: %s jobs, %s skills indexed",
            indexed_jobs,
            indexed_skills,
        )
    except Exception as exc:
        logger.error(
            "Failed to rebuild vector store (retrieval features may be unavailable). "
            "Cause: %s",
            exc,
            exc_info=True,
        )
        logger.error(
            "If the embedding model '%s' could not be downloaded, please check your "
            "network connection or set HF_ENDPOINT / HF_HUB_OFFLINE appropriately.",
            get_settings().embedding_model,
        )
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 模块直接运行时默认不重建向量库，避免在缺少 Embedding 模型或受限网络环境中失败；
    # 如需重建向量库，请显式调用 init_db(rebuild_vector_store=True)。
    init_db(rebuild_vector_store=False)
