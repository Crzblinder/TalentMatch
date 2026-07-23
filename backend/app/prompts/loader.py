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
        backend/app/prompts/{agent_name}/{version}/{variant}.txt

    支持变体：zero_shot / cot / few_shot / roleplay / fresh_graduate
    当指定变体文件不存在时，自动 fallback 到 zero_shot。
    若配置了 prompt_version，优先尝试版本化目录，再回退到未版本化目录。
    """

    def load(
        self,
        agent_name: str,
        variant: str = "zero_shot",
        *,
        version: str | None = None,
    ) -> str:
        """读取提示词文件内容，返回完整文本。

        Args:
            agent_name: Agent 名称，如 jd_parser / talent_matcher / trend_predictor /
                        learning_planner / skill_advisor
            variant:    策略变体，如 zero_shot / cot / few_shot / roleplay
            version:    提示词版本，如 v1 / v2；为空则保持向后兼容

        Returns:
            提示词纯文本内容。
        """
        normalized = _VARIANT_ALIASES.get(variant, variant)
        version = (version or "").strip()

        candidates: list[Path] = []
        if version:
            candidates.append(_PROMPTS_ROOT / agent_name / version / f"{normalized}.txt")
            candidates.append(_PROMPTS_ROOT / agent_name / version / "zero_shot.txt")
        candidates.append(_PROMPTS_ROOT / agent_name / f"{normalized}.txt")
        candidates.append(_PROMPTS_ROOT / agent_name / "zero_shot.txt")

        for file_path in candidates:
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8").strip()
                logger.debug("已加载提示词：%s（%d 字符）", file_path, len(content))
                return content

        # 统一给出清晰的错误信息
        searched = ", ".join(str(p.relative_to(_PROMPTS_ROOT)) for p in candidates)
        raise FileNotFoundError(
            f"Agent '{agent_name}' 的提示词文件未找到（变体={variant}, 版本={version or '默认'}）；"
            f"已搜索：{searched}"
        )
