from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


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

    model_config = ConfigDict(
        env_file=".env",
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
