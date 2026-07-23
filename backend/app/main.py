import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app import models  # noqa: F401  注册所有模型到 Base.metadata
from app.api.health import run_health_checks, run_liveness_check, run_readiness_check
from app.api.metrics import generate_metrics
from app.api.routes import api_router
from app.config import get_settings
from app.init_db import _ensure_columns
from app.models.base import Base, engine
from app.scheduler import shutdown_scheduler, start_scheduler

settings = get_settings()


def _configure_logging() -> Any:
    """配置结构化日志：开发环境可读，生产环境 JSON。"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    is_development = settings.app_env == "development"

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if is_development:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_traceback,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 同步标准库日志到 structlog 处理器，确保第三方库日志也走统一格式
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True)
            if is_development
            else structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # 保留 uvicorn 访问日志但降低重复输出
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.addHandler(handler)
        uvicorn_logger.setLevel(log_level)
        uvicorn_logger.propagate = False

    return structlog.get_logger("app")


logger = _configure_logging()

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


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """为每个请求生成 request_id 并写入日志上下文。"""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


app.include_router(api_router, prefix="/api/v1")


@app.get("/metrics")
def metrics():
    """Prometheus 指标暴露端点。"""
    data, content_type = generate_metrics()
    return Response(content=data, media_type=content_type)


@app.get("/health")
def health_check():
    """聚合健康检查：返回数据库、Redis、向量库、LLM、搜索等状态。"""
    report = run_health_checks(settings)
    return {
        "status": report.status,
        "checked_at": report.checked_at,
        "env": settings.app_env,
        "checks": [
            {
                "name": c.name,
                "status": c.status,
                "message": c.message,
                "response_time_ms": c.response_time_ms,
                "detail": c.detail,
            }
            for c in report.checks
        ],
    }


@app.get("/health/live")
def health_live():
    """存活探针。"""
    report = run_liveness_check()
    return {"status": report.status, "checked_at": report.checked_at}


@app.get("/health/ready")
def health_ready():
    """就绪探针：关键依赖可用时返回 200，否则返回 503。"""
    report = run_readiness_check(settings)
    http_status = (
        status.HTTP_200_OK
        if report.status == "ok"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        status_code=http_status,
        content={
            "status": report.status,
            "checked_at": report.checked_at,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "response_time_ms": c.response_time_ms,
                    "detail": c.detail,
                }
                for c in report.checks
            ],
        },
    )
