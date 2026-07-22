# ruff: noqa: E501
"""
Agent 提示词注册表 —— 用于 A/B 测试与评估。

所有提示词文本已外置到 backend/app/prompts/{agent_name}/{variant}.txt，
本模块仅维护变体元数据注册表，template 字段通过 PromptLoader 懒加载。
如需修改提示词内容，请直接编辑对应的 .txt 文件。
"""

from app.prompts.loader import PromptLoader

_loader = PromptLoader()


def _lazy_template(agent_type: str, variant_file: str) -> str:
    """从外部文件懒加载提示词模板。"""
    return _loader.load(agent_type, variant_file)


# Registry of prompt variants for A/B testing
PROMPT_VARIANTS = [
    {"name": "jd_parser-zero-shot", "agent_type": "jd_parser", "technique": "Zero-Shot", "is_baseline": 1, "variant_file": "zero_shot"},
    {"name": "jd_parser-cot", "agent_type": "jd_parser", "technique": "CoT", "is_baseline": 0, "variant_file": "cot"},
    {"name": "jd_parser-few-shot", "agent_type": "jd_parser", "technique": "Few-Shot", "is_baseline": 0, "variant_file": "few_shot"},
    {"name": "talent_matcher-zero-shot", "agent_type": "talent_matcher", "technique": "Zero-Shot", "is_baseline": 1, "variant_file": "zero_shot"},
    {"name": "talent_matcher-cot", "agent_type": "talent_matcher", "technique": "CoT", "is_baseline": 0, "variant_file": "cot"},
    {"name": "talent_matcher-few-shot", "agent_type": "talent_matcher", "technique": "Few-Shot", "is_baseline": 0, "variant_file": "few_shot"},
    {"name": "trend_predictor-zero-shot", "agent_type": "trend_predictor", "technique": "Zero-Shot", "is_baseline": 1, "variant_file": "zero_shot"},
    {"name": "trend_predictor-cot", "agent_type": "trend_predictor", "technique": "CoT", "is_baseline": 0, "variant_file": "cot"},
    {"name": "trend_predictor-few-shot", "agent_type": "trend_predictor", "technique": "Few-Shot", "is_baseline": 0, "variant_file": "few_shot"},
    {"name": "learning_planner-zero-shot", "agent_type": "learning_planner", "technique": "Zero-Shot", "is_baseline": 1, "variant_file": "zero_shot"},
    {"name": "learning_planner-cot", "agent_type": "learning_planner", "technique": "CoT", "is_baseline": 0, "variant_file": "cot"},
    {"name": "learning_planner-few-shot", "agent_type": "learning_planner", "technique": "Few-Shot", "is_baseline": 0, "variant_file": "few_shot"},
    {"name": "skill_advisor-zero-shot", "agent_type": "skill_advisor", "technique": "Zero-Shot", "is_baseline": 1, "variant_file": "zero_shot"},
    {"name": "skill_advisor-cot", "agent_type": "skill_advisor", "technique": "CoT", "is_baseline": 0, "variant_file": "cot"},
    {"name": "skill_advisor-few-shot", "agent_type": "skill_advisor", "technique": "Few-Shot", "is_baseline": 0, "variant_file": "few_shot"},
]


def get_template(variant_name: str) -> str:
    """根据变体名称（如 'jd_parser-zero-shot'）获取提示词模板文本。"""
    for v in PROMPT_VARIANTS:
        if v["name"] == variant_name:
            return _lazy_template(v["agent_type"], v["variant_file"])
    raise ValueError(f"Unknown prompt variant: {variant_name}")
