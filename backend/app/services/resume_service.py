"""简历解析服务。"""

from __future__ import annotations

import base64
import io
import logging
import os
import re
from typing import Any

import requests
from docx import Document
from PyPDF2 import PdfReader

from app.agents.resume_parser import ResumeParser
from app.config import get_settings
from app.utils.content_safety import check_text_safety, mask_resume_data

logger = logging.getLogger(__name__)


def should_use_fuzzy_parsing(text: str, content_type: "resume" | "jd") -> bool:
    """根据文本内容自动判断是否启用模糊解析。

    规则优先级：
    1. 若存在明确的社招/资深信号，直接判定为非模糊；
    2. 若存在应届生/在校生/边界不清信号，判定为模糊；
    3. 其余情况默认非模糊。

    Args:
        text: 原始文本内容
        content_type: 内容类型，"resume" 或 "jd"

    Returns:
        是否建议启用模糊解析
    """
    if not text or not isinstance(text, str):
        return False

    if content_type == "resume":
        # 明确的社招/资深信号：有清晰工作经历的简历不需要模糊解析
        senior_signals = [
            "工作经历",
            "工作经验",
            "年以上",
            "年经验",
            "资深",
            "高级",
            "专家",
            "总监",
            "经理",
            "主管",
        ]
        has_senior_signal = any(signal in text for signal in senior_signals)

        # 应届生/在校生/项目型简历关键词
        fresh_grad_signals = [
            "在校",
            "实习",
            "应届生",
            "毕业生",
            "课程设计",
            "毕业设计",
        ]
        has_fresh_grad_signal = any(signal in text for signal in fresh_grad_signals)

        # 匹配 "202x届" 毕业年份
        has_grad_year = bool(re.search(r"202\d届", text))

        # 项目经历单独作为弱信号：仅当同时缺少明确工作经历时才触发模糊
        has_projects = "项目" in text
        lacks_work_section = "工作经历" not in text and "工作经验" not in text

        if has_senior_signal:
            return False
        if has_fresh_grad_signal or has_grad_year:
            return True
        if has_projects and lacks_work_section:
            return True
        # 文本过短且没有任何社招信号，保守启用模糊
        if len(text) < 200 and not has_senior_signal:
            return True

        return False

    if content_type == "jd":
        # 明确的应届生友好信号
        fresh_grad_signals = [
            "应届生",
            "校招",
            "实习生",
            "接受零基础",
            "经验不限",
            "优秀毕业生",
            "毕业生优先",
            "无经验",
        ]
        has_fresh_grad_signal = any(signal in text for signal in fresh_grad_signals)

        # 明确的资深/社招信号
        senior_signals = [
            "年以上",
            "年经验",
            "资深",
            "高级",
            "专家",
            "总监",
            "管理经验",
        ]
        has_senior_signal = any(signal in text for signal in senior_signals)

        # 要求描述宽泛/模糊的线索
        vague_clues = ["相关专业优先", "可接受", "不限专业", "亦可"]
        has_vague_clue = any(clue in text for clue in vague_clues)

        if has_senior_signal and not has_fresh_grad_signal:
            return False
        if has_fresh_grad_signal or has_vague_clue:
            return True

        return False

    return False


class ResumeService:
    """简历上传与解析服务。"""

    def _parse_with_dashscope(self, file_bytes: bytes, filename: str) -> str:
        """调用阿里云百炼 DashScope 文档解析 API。

        图片/PDF 使用多模态模型 qwen-vl-max 进行 OCR；DOCX 等文档使用
        qwen-long 文件上传能力解析。失败时抛出异常，由调用方降级到本地解析。
        """
        settings = get_settings()
        api_key = settings.dashscope_api_key
        base_url = settings.dashscope_base_url.rstrip("/")
        model = settings.dashscope_doc_parse_model
        ext = os.path.splitext(filename)[1].lower()

        mime_map = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
        }
        mime = mime_map.get(ext, "application/octet-stream")

        headers = {"Authorization": f"Bearer {api_key}"}

        # 图片/PDF 使用 qwen-vl-max vision 能力（OpenAI-compatible）
        if mime.startswith("image/") or mime == "application/pdf":
            logger.info("使用 DashScope vision 模型 %s 解析 %s", model, filename)
            encoded = base64.b64encode(file_bytes).decode("utf-8")
            data_url = f"data:{mime};base64,{encoded}"
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是文档识别专家。请提取用户上传文件中的全部文本内容，"
                            "保留原有段落和列表结构，以 Markdown 格式返回。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请识别并提取以下文件中的全部文本内容：",
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
            }
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={**headers, "Content-Type": "application/json"},
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"].get("content", "")
            if not content:
                raise ValueError("DashScope vision 解析返回空内容")
            logger.info("DashScope vision 解析成功: %s", filename)
            return content.strip()

        # DOCX 等文档使用 qwen-long 文件上传能力
        logger.info("使用 DashScope qwen-long 文件上传解析 %s", filename)
        upload_resp = requests.post(
            f"{base_url}/files",
            headers=headers,
            files={"file": (filename, io.BytesIO(file_bytes), mime)},
            data={"purpose": "user_data"},
            timeout=60,
        )
        upload_resp.raise_for_status()
        file_id = upload_resp.json().get("id")
        if not file_id:
            raise ValueError("DashScope 文件上传未返回 file_id")

        payload = {
            "model": "qwen-long",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是文档识别专家。请提取用户上传文件中的全部文本内容，"
                        "保留原有段落和列表结构，以 Markdown 格式返回。"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"file": file_id},
                        {"type": "text", "text": "请识别并提取文件中的全部文本内容。"},
                    ],
                },
            ],
        }
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"].get("content", "")
        if not content:
            raise ValueError("DashScope 文件解析返回空内容")
        logger.info("DashScope qwen-long 解析成功: %s", filename)
        return content.strip()

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """从 PDF 字节流中提取文本。

        开启国产模型且配置了 DASHSCOPE_API_KEY 时，优先调用 DashScope 云端解析；
        失败或未配置时自动降级到本地 PyPDF2 解析。
        """
        settings = get_settings()
        if settings.use_domestic_llm and settings.dashscope_api_key:
            try:
                logger.info("PDF 优先使用 DashScope 云端解析")
                return self._parse_with_dashscope(file_bytes, "document.pdf")
            except Exception as exc:
                logger.warning("DashScope PDF 解析失败，降级本地解析: %s", exc)
        else:
            logger.info("PDF 使用本地 PyPDF2 解析")

        text_parts: list[str] = []
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
        return "\n".join(text_parts).strip()

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """从 DOCX 字节流中提取文本。

        开启国产模型且配置了 DASHSCOPE_API_KEY 时，优先调用 DashScope 云端解析；
        失败或未配置时自动降级到本地 python-docx 解析。
        """
        settings = get_settings()
        if settings.use_domestic_llm and settings.dashscope_api_key:
            try:
                logger.info("DOCX 优先使用 DashScope 云端解析")
                return self._parse_with_dashscope(file_bytes, "document.docx")
            except Exception as exc:
                logger.warning("DashScope DOCX 解析失败，降级本地解析: %s", exc)
        else:
            logger.info("DOCX 使用本地 python-docx 解析")

        document = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in document.paragraphs if p.text]
        return "\n".join(paragraphs).strip()

    def _extract_text(self, file_bytes: bytes, filename: str) -> str:
        """根据文件名扩展名选择 PDF 或 DOCX 文本提取。"""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return self.extract_text_from_pdf(file_bytes)
        if ext == ".docx":
            return self.extract_text_from_docx(file_bytes)
        raise ValueError(f"不支持的文件格式: {ext}")

    def parse_resume(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        fuzzy: bool = False,
        prompt_variant: str | None = None,
    ) -> dict[str, Any]:
        """解析简历文件，返回结构化信息。

        Args:
            file_bytes: 文件字节流
            filename: 文件名（用于判断 PDF/DOCX）
            fuzzy: 是否启用模糊识别（应届生友好模式）
            prompt_variant: 指定提示词变体，默认 fuzzy 为 True 时使用 fresh_graduate
        """
        # 获取文件扩展名并统一小写
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            raw_text = self.extract_text_from_pdf(file_bytes)
        elif ext == ".docx":
            raw_text = self.extract_text_from_docx(file_bytes)
        else:
            raise ValueError("仅支持 PDF 和 DOCX 格式")

        return self.parse_resume_text(
            raw_text,
            fuzzy=fuzzy,
            prompt_variant=prompt_variant,
        )

    def parse_resume_text(
        self,
        raw_text: str,
        *,
        fuzzy: bool = False,
        prompt_variant: str | None = None,
    ) -> dict[str, Any]:
        """直接解析简历文本。"""
        settings = get_settings()

        safety = check_text_safety(raw_text, settings)
        if not safety.get("safe", True):
            labels = safety.get("labels", [])
            logger.warning("简历文本内容安全检测未通过，labels: %s", labels)
            raise ValueError(
                f"简历内容未通过安全检测，违规标签: {', '.join(labels) if labels else '未知'}"
            )

        variant = prompt_variant or ("fresh_graduate" if fuzzy else "default")
        parser = ResumeParser(prompt_variant=variant)
        parsed = parser.parse_resume(raw_text)

        basic = parsed.get("basic_info", {})
        job_intention = parsed.get("job_intention", {})

        # 兼容旧字段，同时返回新的详细字段
        result = {
            # 旧字段兼容
            "name": basic.get("name", ""),
            "skills": parsed.get("skills") or [],
            "experience_level": self._infer_experience_level(parsed),
            "education_level": self._infer_education_level(parsed),
            "raw_text": raw_text,
            # 新增详细字段
            "basic_info": basic,
            "education": parsed.get("education") or [],
            "work_experience": parsed.get("work_experience") or [],
            "project_experience": parsed.get("project_experience") or [],
            "awards": parsed.get("awards") or [],
            "certifications": parsed.get("certifications") or [],
            "language_skills": parsed.get("language_skills") or [],
            "self_evaluation": parsed.get("self_evaluation", ""),
            "job_intention": job_intention,
        }

        if settings.enable_resume_masking:
            logger.info("简历脱敏开关已开启，对解析结果进行脱敏处理")
            result = mask_resume_data(result)

        return result

    def _infer_experience_level(self, parsed: dict[str, Any]) -> str:
        """根据工作/项目经历推断经验级别。"""
        work = parsed.get("work_experience") or []
        projects = parsed.get("project_experience") or []
        total_months = 0
        for item in work + projects:
            start = item.get("start_date", "")
            end = item.get("end_date", "至今")
            months = self._calculate_months(start, end)
            if months and months > 0:
                total_months += months

        if total_months == 0:
            return "应届/在校生"
        if total_months < 12:
            return "应届生"
        if total_months < 36:
            return "1-3年"
        if total_months < 60:
            return "3-5年"
        if total_months < 120:
            return "5-10年"
        return "10年以上"

    def _infer_education_level(self, parsed: dict[str, Any]) -> str:
        """根据教育经历推断最高学历。"""
        educations = parsed.get("education") or []
        level_order = {"博士": 4, "硕士": 3, "本科": 2, "大专": 1}
        best = ""
        best_score = 0
        for edu in educations:
            degree = edu.get("degree", "")
            score = level_order.get(degree, 0)
            if score > best_score:
                best_score = score
                best = degree
        return best or "不限"

    def _calculate_months(self, start: str, end: str) -> int | None:
        """根据起止时间计算月份差。"""
        import re

        m_start = re.search(r"(\d{4})[\.\-/](\d{1,2})", str(start))
        if not m_start:
            return None
        year_s, month_s = int(m_start.group(1)), int(m_start.group(2))

        if str(end) in ("至今", "现在", ""):
            from datetime import datetime

            now = datetime.now()
            year_e, month_e = now.year, now.month
        else:
            m_end = re.search(r"(\d{4})[\.\-/](\d{1,2})", str(end))
            if not m_end:
                return None
            year_e, month_e = int(m_end.group(1)), int(m_end.group(2))

        return (year_e - year_s) * 12 + (month_e - month_s)
