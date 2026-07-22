"""LLMClientFactory 配置与客户端实例化测试。"""

from __future__ import annotations

from app.config import Settings
from app.llm.factory import LLMClientFactory


def test_create_domestic_dashscope():
    """开启国产模式并配置 DashScope 时，优先返回 DashScope 客户端。"""
    settings = Settings(
        use_domestic_llm=True,
        dashscope_api_key="sk-test",
        dashscope_model="qwen-max",
        dashscope_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    client = LLMClientFactory.create(settings)
    assert client.model_name == "qwen-max"
    assert str(client.openai_api_base) == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert client.openai_api_key.get_secret_value() == "sk-test"


def test_create_domestic_zhipu_when_no_dashscope():
    """仅配置 Zhipu 时返回 Zhipu 客户端。"""
    settings = Settings(
        use_domestic_llm=True,
        zhipu_api_key="sk-zhipu",
        zhipu_model="glm-4",
        zhipu_base_url="https://open.bigmodel.cn/api/paas/v4",
    )
    client = LLMClientFactory.create(settings)
    assert client.model_name == "glm-4"
    assert str(client.openai_api_base) == "https://open.bigmodel.cn/api/paas/v4"
    assert client.openai_api_key.get_secret_value() == "sk-zhipu"


def test_create_fallback_openai_when_domestic_disabled():
    """未开启国产模式时保持原有 OpenAI-compatible 行为。"""
    settings = Settings(
        use_domestic_llm=False,
        openai_api_key="",
        openai_model="gpt-4o-mini",
        openai_base_url="https://api.openai.com/v1",
    )
    client = LLMClientFactory.create(settings)
    assert client.model_name == "gpt-4o-mini"
    assert str(client.openai_api_base) == "https://api.openai.com/v1"
    assert client.openai_api_key.get_secret_value() == "dummy"


def test_create_fallback_openai_when_domestic_enabled_but_no_key():
    """开启国产模式但未配置任何国产 Key 时，降级到 OpenAI-compatible。"""
    settings = Settings(
        use_domestic_llm=True,
        dashscope_api_key="",
        zhipu_api_key="",
        openai_api_key="sk-openai",
        openai_model="gpt-4o-mini",
        openai_base_url="https://api.openai.com/v1",
    )
    client = LLMClientFactory.create(settings)
    assert client.model_name == "gpt-4o-mini"
    assert str(client.openai_api_base) == "https://api.openai.com/v1"
    assert client.openai_api_key.get_secret_value() == "sk-openai"


def test_create_multimodal_domestic():
    """开启国产模式时，多模态客户端使用国产多模态模型与 DashScope Key。"""
    settings = Settings(
        use_domestic_llm=True,
        dashscope_api_key="sk-test",
        domestic_multimodal_model="qwen-vl-max",
        dashscope_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    client = LLMClientFactory.create_multimodal(settings)
    assert client.model_name == "qwen-vl-max"
    assert str(client.openai_api_base) == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert client.openai_api_key.get_secret_value() == "sk-test"


def test_create_multimodal_openai_when_domestic_disabled():
    """未开启国产模式时，多模态客户端保持原有 OpenAI 逻辑。"""
    settings = Settings(
        use_domestic_llm=False,
        multimodal_model="gpt-4o",
        multimodal_api_key="",
        openai_api_key="sk-openai",
        openai_base_url="https://api.openai.com/v1",
    )
    client = LLMClientFactory.create_multimodal(settings)
    assert client.model_name == "gpt-4o"
    assert str(client.openai_api_base) == "https://api.openai.com/v1"
    assert client.openai_api_key.get_secret_value() == "sk-openai"
