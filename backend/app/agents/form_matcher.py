import json
import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class FormMatcher(BaseAgent):
    """网申表单字段智能匹配 Agent。

    将招聘网站申请表中的字段（label、name、placeholder 等）与用户的简历画像
    进行语义匹配，返回每个字段应填入的值及置信度。
    """

    name = "form_matcher"

    def match_fields(
        self,
        fields: list[dict[str, Any]],
        profile: dict[str, Any],
        jd_text: str | None = None,
    ) -> dict[str, Any]:
        """匹配表单字段与简历数据。

        Args:
            fields: 从页面提取的表单字段列表，每项包含 id、name、label、
                type、placeholder、selector、required 等。
            profile: 用户画像/简历结构化数据。
            jd_text: 可选的岗位描述文本，用于提升匹配准确度。

        Returns:
            {"matches": [{"field_id", "value", "confidence", "reason"}], "unmatched": [...]}
        """
        system_prompt = self._load_prompt()
        user_prompt = self._build_user_prompt(fields, profile, jd_text)

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )

        if result.get("simulated"):
            return self._fallback_match(fields, profile)

        return self._normalize_result(result, fields)

    def _build_user_prompt(
        self,
        fields: list[dict[str, Any]],
        profile: dict[str, Any],
        jd_text: str | None,
    ) -> str:
        jd_section = f"""\n## 目标岗位描述\n{jd_text}\n""" if jd_text else ""

        return f"""请将以下网申表单字段与简历数据进行智能匹配。

## 表单字段
{json.dumps(fields, ensure_ascii=False, indent=2)}

## 简历数据
{json.dumps(profile, ensure_ascii=False, indent=2)}
{jd_section}
## 匹配要求
1. 逐个分析表单字段的真实意图（字段标签、name、placeholder、 surrounding text）。
2. 从简历数据中选择最合适的内容填入，支持跨字段推理
   （如“姓名”对应 basic_info.name，“手机”对应 basic_info.phone）。
3. 对无法匹配的字段，输出空值并说明原因。
4. 对存在歧义的字段（如“经历”可能指工作或项目经历），
   结合岗位描述或字段上下文给出最佳推断。
5. 返回 JSON 数组，每项包含：field_id（对应输入字段 id）、value（要填入的字符串）、
   confidence（high/medium/low）、reason（简短理由）。

请直接输出 JSON，不要包含 Markdown 代码块。"""

    def _normalize_result(
        self,
        result: dict[str, Any],
        fields: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """规范化 LLM 匹配结果。"""
        matches = []
        unmatched = []
        field_ids = {str(f.get("id", "")) for f in fields}

        raw_matches = result.get("matches") or []
        if isinstance(raw_matches, dict):
            raw_matches = [
                {"field_id": k, "value": v, "confidence": "medium", "reason": ""}
                for k, v in raw_matches.items()
            ]

        seen = set()
        for item in raw_matches:
            field_id = str(item.get("field_id", ""))
            if not field_id or field_id not in field_ids or field_id in seen:
                continue
            seen.add(field_id)
            matches.append({
                "field_id": field_id,
                "value": str(item.get("value", "")),
                "confidence": item.get("confidence", "medium"),
                "reason": item.get("reason", ""),
            })

        for f in fields:
            fid = str(f.get("id", ""))
            if fid and fid not in seen:
                unmatched.append({
                    "field_id": fid,
                    "label": f.get("label", ""),
                    "name": f.get("name", ""),
                    "reason": "未匹配到合适简历数据",
                })

        return {"matches": matches, "unmatched": unmatched}

    def _fallback_match(
        self,
        fields: list[dict[str, Any]],
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        """无 LLM 时的规则降级匹配。"""
        from app.services.application_service import rule_based_field_value

        matches = []
        unmatched = []
        for f in fields:
            fid = str(f.get("id", ""))
            value, confidence = rule_based_field_value(f, profile)
            if value:
                matches.append({
                    "field_id": fid,
                    "value": value,
                    "confidence": confidence,
                    "reason": "规则引擎匹配（LLM 未配置）",
                })
            else:
                unmatched.append({
                    "field_id": fid,
                    "label": f.get("label", ""),
                    "name": f.get("name", ""),
                    "reason": "规则引擎未命中",
                })
        return {"matches": matches, "unmatched": unmatched}

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        return self.match_fields(
            fields=context.get("fields", []),
            profile=context.get("profile", {}),
            jd_text=context.get("jd_text"),
        )
