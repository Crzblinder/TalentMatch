import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.prompts.loader import PromptLoader

logger = logging.getLogger(__name__)


class LLMToolCallError(Exception):
    """LLM function calling 相关错误。"""


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, prompt_variant: str | None = None):
        self.settings = get_settings()
        self.prompt_variant = prompt_variant or "default"
        self._llm = None  # 延迟初始化 LangChain BaseChatModel
        self.loader = PromptLoader()

    # ------------------------------------------------------------------
    # LLM 客户端（懒加载，通过工厂统一创建）
    # ------------------------------------------------------------------
    @property
    def llm(self):
        if self._llm is None:
            from app.llm.factory import LLMClientFactory

            self._llm = LLMClientFactory.create(self.settings)
        return self._llm

    # ------------------------------------------------------------------
    # 是否具备真实 LLM 调用能力
    # ------------------------------------------------------------------
    def _has_real_llm(self) -> bool:
        if self.settings.use_local_llm:
            # Ollama 模式下，只要地址配置了即视为可用
            return bool(self.settings.ollama_base_url)
        return bool(self.settings.openai_api_key and self.settings.openai_api_key != "dummy")

    # ------------------------------------------------------------------
    # 标准化链式调用（提示词组装 -> LLM -> JSON 解析 -> 容灾降级）
    # ------------------------------------------------------------------
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        response_format: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """通过 LangChain 统一接口调用大模型，强制 JSON 输出，异常时降级到规则引擎。"""
        from langchain_core.messages import HumanMessage, SystemMessage

        start = time.time()

        # ---- 无 LLM 配置时直接走确定性降级 ----
        if not self._has_real_llm():
            logger.warning("No LLM configured (use_local_llm=%s); deterministic fallback",
                           self.settings.use_local_llm)
            return self._simulate_response(system_prompt, user_prompt)

        # ---- 组装 LangChain 消息列表 ----
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            # 通过 LangChain BaseChatModel 统一调用
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)

            elapsed_ms = int((time.time() - start) * 1000)
            parsed = self._parse_json(content)
            parsed["_latency_ms"] = elapsed_ms

            # 若 JSON 解析失败（返回了 raw wrapper），视为异常触发降级
            if parsed.get("parsed") is False:
                logger.warning("LLM returned non-JSON content; triggering fallback")
                fallback = self._simulate_response(system_prompt, user_prompt)
                fallback["_latency_ms"] = elapsed_ms
                fallback["_fallback_reason"] = "non_json_response"
                return fallback

            return parsed

        except Exception as e:
            logger.error("LLM call failed: %s; triggering deterministic fallback", e)
            elapsed_ms = int((time.time() - start) * 1000)
            fallback = self._simulate_response(system_prompt, user_prompt)
            fallback["_latency_ms"] = elapsed_ms
            fallback["_fallback_reason"] = str(e)
            return fallback

    # ------------------------------------------------------------------
    # Function Calling / Tool Use 支持
    # ------------------------------------------------------------------
    def call_llm_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[Any] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        temperature: float = 0.3,
        max_iterations: int = 3,
    ) -> dict[str, Any]:
        """调用支持 function calling 的 LLM，可自动执行工具并返回最终结果。

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            tools: LangChain Tool 列表；为 None 时使用默认求职工具集
            tool_choice: 工具选择策略，默认 auto
            temperature: 采样温度
            max_iterations: 最大工具调用轮数，防止循环

        Returns:
            {"content": str, "tool_calls": list, "tool_results": list}
        """
        from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

        if not self._has_real_llm():
            logger.warning("No LLM configured; skip function calling")
            return {
                "content": "",
                "tool_calls": [],
                "tool_results": [],
                "simulated": True,
                "note": "LLM not configured; function calling skipped",
            }

        if tools is None:
            from app.agents.tools import get_langchain_tools

            tools = get_langchain_tools()

        try:
            llm_with_tools = self.llm.bind_tools(tools, tool_choice=tool_choice)
        except Exception as exc:
            logger.warning("LLM does not support tool binding: %s", exc)
            return {
                "content": "",
                "tool_calls": [],
                "tool_results": [],
                "error": f"tool_binding_failed: {exc}",
            }

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        tool_calls_log: list[dict[str, Any]] = []
        tool_results_log: list[dict[str, Any]] = []

        for _ in range(max_iterations):
            response = llm_with_tools.invoke(messages)
            content = response.content if hasattr(response, "content") else ""

            tool_calls = response.tool_calls if hasattr(response, "tool_calls") else []
            if not tool_calls:
                return {
                    "content": str(content),
                    "tool_calls": tool_calls_log,
                    "tool_results": tool_results_log,
                }

            messages.append(response)
            for call in tool_calls:
                tool_calls_log.append({
                    "name": call.get("name"),
                    "args": call.get("args"),
                })
                from app.agents.tools import execute_tool_call

                result = execute_tool_call(
                    name=call.get("name", ""),
                    arguments=call.get("args") or {},
                )
                tool_results_log.append({
                    "name": call.get("name"),
                    "result": result,
                })
                messages.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False, default=str),
                        tool_call_id=call.get("id", "unknown"),
                    )
                )

        # 达到最大迭代次数后，再调用一次获取最终总结
        final_response = llm_with_tools.invoke(messages)
        final_content = final_response.content if hasattr(final_response, "content") else ""
        return {
            "content": str(final_content),
            "tool_calls": tool_calls_log,
            "tool_results": tool_results_log,
        }

    # ------------------------------------------------------------------
    # JSON 解析（保留原有逻辑）
    # ------------------------------------------------------------------
    def _parse_json(self, content: str) -> dict[str, Any]:
        content = content.strip()
        # 去除 Markdown 代码块包裹
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM did not return valid JSON; wrapping raw text")
            return {"raw": content, "parsed": False}

    # ------------------------------------------------------------------
    # 确定性降级基类实现（各子类可覆盖）
    # ------------------------------------------------------------------
    def _simulate_response(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Deterministic fallback when no LLM key is provided, so the project runs out-of-box."""
        return {"simulated": True, "note": "LLM not configured; deterministic fallback used"}

    # ------------------------------------------------------------------
    # 提示词加载（从外部 .txt 文件读取）
    # ------------------------------------------------------------------
    def _load_prompt(self) -> str:
        """根据 Agent 名称和当前变体，从外部文件加载提示词模板。"""
        variant = self._resolve_variant()
        return self.loader.load(self.name, variant)

    def _resolve_variant(self) -> str:
        """将 prompt_variant 标准化为文件名格式。"""
        v = self.prompt_variant or "default"
        # 将 "scanner-zero-shot" 这类全名转换为 "zero_shot"
        if "-" in v:
            parts = v.split("-", 1)
            if len(parts) == 2:
                v = parts[1]
        # 标准化映射
        aliases = {
            "default": "zero_shot",
            "zero-shot": "zero_shot",
            "Zero-Shot": "zero_shot",
            "cot": "cot",
            "CoT": "cot",
            "few-shot": "few_shot",
            "Few-Shot": "few_shot",
            "roleplay": "roleplay",
            "RolePlay": "roleplay",
        }
        return aliases.get(v, v)

    @abstractmethod
    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
