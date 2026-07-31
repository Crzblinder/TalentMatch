from functools import lru_cache
from pathlib import Path

from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings

# 项目根目录（backend 的父目录）
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # LLM — 通用
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # LLM — 多模态模型配置（用于图片/OCR/文档分析）
    multimodal_model: str = "gpt-4o"
    multimodal_api_key: str = ""
    multimodal_base_url: str = ""

    # LLM — 国产大模型（OpenAI-compatible）
    use_domestic_llm: bool = False
    dashscope_api_key: str = ""
    dashscope_model: str = "qwen-max"
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    zhipu_api_key: str = ""
    zhipu_model: str = "glm-4"
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"

    # LLM — 国产多模态模型（use_domestic_llm=true 时优先使用）
    domestic_multimodal_model: str = "qwen-vl-max"

    # 文档解析：优先使用的国产多模态/OCR 模型
    dashscope_doc_parse_model: str = "qwen-vl-max"

    # LLM — 模式开关：true 走 Ollama，false 走 OpenAI-compatible API
    use_local_llm: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # 智能体编排：默认使用 LangGraph 图引擎
    use_langgraph: bool = True

    # Database
    database_url: str = "sqlite:///./talentmatch.db"
    database_url_sqlite: str = "sqlite:///./talentmatch.db"

    # Vector store
    vector_db_path: str = "./chroma_data"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    vector_db_provider: str = "chroma"  # chroma | qdrant
    qdrant_url: str = "http://localhost:6333"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False  # 测试环境可设为 true 同步执行任务

    # 联网搜索配置（可选）
    # 默认使用 DuckDuckGo（无需 API Key）；如需更稳定结果可配置 Tavily
    tavily_api_key: str = ""
    search_default_intent: str = "general"

    # 国产化搜索源（可选，按 Bocha -> 智谱 -> SearXNG -> Tavily -> DuckDuckGo 优先级）
    bocha_api_key: str = ""
    searxng_base_url: str = "http://localhost:8080"

    # 定时采集任务（默认关闭，避免开发环境意外启动）
    scheduler_enabled: bool = False
    fetch_interval_hours: int = 6

    # 国内招聘平台抓取（默认关闭，避免开发/测试环境触发反爬）
    domestic_crawler_enabled: bool = False
    playwright_headless: bool = True
    domestic_crawler_delay_ms: int = 1000

    # 内容安全（阿里云绿网/内容安全）
    enable_content_safety: bool = False
    alibaba_cloud_access_key_id: str = ""
    alibaba_cloud_access_key_secret: str = ""
    content_safety_endpoint: str = "green-cip.cn-shanghai.aliyuncs.com"

    # 简历数据脱敏
    enable_resume_masking: bool = False

    # 提示词版本：默认使用未版本化的提示词，可指定如 v1、v2 等
    prompt_version: str = ""

    # 告警通知
    alert_enabled: bool = False
    alert_llm_failure_rate_threshold: float = 0.3
    alert_rss_fetch_failure_rate_threshold: float = 0.5
    alert_parse_failure_rate_threshold: float = 0.3
    alert_email_smtp_host: str = ""
    alert_email_smtp_port: int = 587
    alert_email_smtp_user: str = ""
    alert_email_smtp_password: str = ""
    alert_email_to: str = ""  # 多个收件人用逗号分隔
    alert_webhook_url: str = ""

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        """启动时校验关键安全配置。"""
        import logging
        import sys

        logger = logging.getLogger(__name__)
        errors: list[str] = []
        warnings: list[str] = []

        # SECRET_KEY 校验
        secret_key = self.secret_key
        if not secret_key or secret_key.strip() == "" or secret_key == "change-me-in-production":
            msg = (
                "SECRET_KEY 为空或使用了危险默认值。"
                "请运行 `openssl rand -hex 32` 生成强密钥并设置到环境变量 SECRET_KEY。"
            )
            if self.app_env == "production":
                errors.append(msg)
            else:
                warnings.append(msg)

        # 生产环境数据库校验
        if self.app_env == "production":
            db_url = self.effective_database_url.lower()
            if "sqlite" in db_url:
                errors.append(
                    "生产环境不允许使用 SQLite。"
                    "请配置 MySQL/PostgreSQL 数据库连接字符串（如 DATABASE_URL=mysql+pymysql://...）"
                )

        # 敏感配置最小长度校验
        if self.app_env == "production":
            if len(secret_key) < 32:
                errors.append("生产环境 SECRET_KEY 长度至少 32 位。")

        for warning in warnings:
            logger.error("[SECURITY WARNING] %s", warning)

        if errors:
            for error in errors:
                logger.error("[SECURITY ERROR] %s", error)
            sys.exit(1)

        return self

    model_config = ConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_database_url(self) -> str:
        # Prefer MySQL when available; fallback to SQLite for quick local runs
        if "mysql" in self.database_url.lower():
            return self.database_url
        return self.database_url_sqlite

    @property
    def effective_multimodal_api_key(self) -> str:
        return self.multimodal_api_key or self.openai_api_key

    @property
    def effective_multimodal_base_url(self) -> str:
        return self.multimodal_base_url or self.openai_base_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
