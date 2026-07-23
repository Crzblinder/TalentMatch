import json
import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.prompts.loader import PromptLoader

logger = structlog.get_logger("app.agents")

try:
    from app.api.metrics import record_llm_call
except Exception:  # pragma: no cover - 允许未安装 prometheus_client 时降级
    def record_llm_call(agent: str, duration_ms: float, success: bool) -> None:  # noqa: ARG001
        """Metrics 不可用时的空实现。"""


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
    # 日志辅助方法
    # ------------------------------------------------------------------
    def _resolve_model_name(self) -> str:
        """返回当前实际使用的模型名，用于结构化日志。"""
        if self.settings.use_local_llm:
            return self.settings.ollama_model
        if self.settings.use_domestic_llm:
            return self.settings.dashscope_model or self.settings.zhipu_model
        return self.settings.openai_model

    @staticmethod
    def _summarize_output(parsed: dict[str, Any]) -> str:
        """对 LLM 输出做简短摘要，避免日志过长。"""
        if not parsed:
            return "empty"
        # 优先取代表性字段
        for key in ("summary", "analysis_summary", "note", "raw"):
            value = parsed.get(key)
            if isinstance(value, str) and value:
                return value[:80] + "..." if len(value) > 80 else value
        return "structured_json"

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
        agent_name = self.name or "unknown"
        model_name = self._resolve_model_name()
        input_length = len(system_prompt) + len(user_prompt)

        logger.info(
            "agent_call_started",
            agent=agent_name,
            model=model_name,
            input_length=input_length,
            temperature=temperature,
        )

        # ---- 无 LLM 配置时直接走确定性降级 ----
        if not self._has_real_llm():
            elapsed_ms = int((time.time() - start) * 1000)
            logger.warning(
                "agent_fallback",
                agent=agent_name,
                reason="llm_not_configured",
                use_local_llm=self.settings.use_local_llm,
                duration_ms=elapsed_ms,
            )
            record_llm_call(agent_name, elapsed_ms, success=False)
            fallback = self._simulate_response(system_prompt, user_prompt)
            fallback["_latency_ms"] = elapsed_ms
            fallback["_fallback_reason"] = "llm_not_configured"
            return fallback

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
            output_summary = self._summarize_output(parsed)

            logger.info(
                "agent_call_completed",
                agent=agent_name,
                model=model_name,
                input_length=input_length,
                output_length=len(content),
                output_summary=output_summary,
                duration_ms=elapsed_ms,
            )

            # 若 JSON 解析失败（返回了 raw wrapper），视为异常触发降级
            if parsed.get("parsed") is False:
                logger.warning(
                    "agent_fallback",
                    agent=agent_name,
                    reason="non_json_response",
                    duration_ms=elapsed_ms,
                )
                record_llm_call(agent_name, elapsed_ms, success=False)
                fallback = self._simulate_response(system_prompt, user_prompt)
                fallback["_latency_ms"] = elapsed_ms
                fallback["_fallback_reason"] = "non_json_response"
                return fallback

            record_llm_call(agent_name, elapsed_ms, success=True)
            return parsed

        except Exception as exc:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.exception(
                "agent_call_failed",
                agent=agent_name,
                model=model_name,
                exception_type=type(exc).__name__,
                duration_ms=elapsed_ms,
            )
            record_llm_call(agent_name, elapsed_ms, success=False)
            fallback = self._simulate_response(system_prompt, user_prompt)
            fallback["_latency_ms"] = elapsed_ms
            fallback["_fallback_reason"] = str(exc)
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
            logger.warning("tool_call_fallback", reason="llm_not_configured")
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
            logger.warning("tool_binding_failed", exception_type=type(exc).__name__, error=str(exc))
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
        """根据 Agent 名称、当前变体和配置版本，从外部文件加载提示词模板。"""
        variant = self._resolve_variant()
        version = self.settings.prompt_version or None
        return self.loader.load(self.name, variant, version=version)

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
