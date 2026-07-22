import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 提示词文件根目录：backend/app/prompts/
_PROMPTS_ROOT = Path(__file__).resolve().parent

# 变体名称标准化映射：将外部传入的变体名映射到文件名（不含 .txt）
_VARIANT_ALIASES = {
    "default": "zero_shot",
    "zero-shot": "zero_shot",
    "zero_shot": "zero_shot",
    "cot": "cot",
    "few-shot": "few_shot",
    "few_shot": "few_shot",
    "roleplay": "roleplay",
    "fresh_graduate": "fresh_graduate",
}


class PromptLoader:
    """从外部 .txt 文件加载 Agent 提示词。

    文件组织规则：
        backend/app/prompts/{agent_name}/{variant}.txt

    支持变体：zero_shot / cot / few_shot / roleplay
    当指定变体文件不存在时，自动 fallback 到 zero_shot。
    """

    def load(self, agent_name: str, variant: str = "zero_shot") -> str:
        """读取提示词文件内容，返回完整文本。

        Args:
            agent_name: Agent 名称，如 jd_parser / talent_matcher / trend_predictor /
                        learning_planner / skill_advisor
            variant:    策略变体，如 zero_shot / cot / few_shot / roleplay

        Returns:
            提示词纯文本内容。
        """
        normalized = _VARIANT_ALIASES.get(variant, variant)
        file_path = _PROMPTS_ROOT / agent_name / f"{normalized}.txt"

        if not file_path.exists():
            logger.warning(
                "提示词文件不存在：%s，尝试 fallback 到 zero_shot", file_path
            )
            file_path = _PROMPTS_ROOT / agent_name / "zero_shot.txt"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Agent '{agent_name}' 的 zero_shot 基础提示词文件也不存在：{file_path}"
            )

        content = file_path.read_text(encoding="utf-8").strip()
        logger.debug("已加载提示词：%s（%d 字符）", file_path, len(content))
        return content
