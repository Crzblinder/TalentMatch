import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  注册所有模型到 Base.metadata
from app.api.routes import api_router
from app.config import get_settings
from app.init_db import _ensure_columns
from app.models.base import Base, engine
from app.scheduler import shutdown_scheduler, start_scheduler

logger = logging.getLogger(__name__)

settings = get_settings()

# 配置应用日志处理器，确保 lifespan、scheduler 等模块日志在 uvicorn 中可见
_log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
_app_logger = logging.getLogger("app")
_app_logger.setLevel(_log_level)
if not _app_logger.handlers:
    _app_handler = logging.StreamHandler()
    _app_handler.setLevel(_log_level)
    _app_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    _app_logger.addHandler(_app_handler)
    _app_logger.propagate = False

# Ensure vector directory exists
os.makedirs(settings.vector_db_path, exist_ok=True)

# Ensure uploads directory exists
os.makedirs("data/uploads", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables if not exist...")
    _ensure_columns(engine)
    Base.metadata.create_all(bind=engine)

    # 根据配置启动定时岗位采集调度器
    start_scheduler()
    try:
        yield
    finally:
        # 应用关闭时释放调度器资源
        shutdown_scheduler()


app = FastAPI(
    title="岗位技能图谱与人才匹配引擎",
    description="Skill map and talent matching engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.app_env}
