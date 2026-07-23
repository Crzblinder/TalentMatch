"""匹配报告 PDF 生成服务。

使用 ReportLab 生成纯服务端 PDF，避免浏览器端依赖。
中文字体优先使用系统 SimHei / SimSun，回退到 ReportLab 内置 Helvetica（英文可用）。
"""

from __future__ import annotations

import io
import logging
import os
import platform
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


def _find_chinese_font_path() -> str | None:
    """在常见系统路径中查找中文字体文件。"""
    system = platform.system().lower()
    candidates: list[str] = []

    if system == "windows":
        candidates = [
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\msyhbd.ttc",
        ]
    elif system == "darwin":
        candidates = [
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        ]

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _register_chinese_font() -> str:
    """注册中文字体并返回可用于 Paragraph 的字体名。"""
    font_path = _find_chinese_font_path()
    if font_path:
        try:
            font_name = "TalentMatchChinese"
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            logger.debug("Registered Chinese font: %s", font_path)
            return font_name
        except Exception as exc:
            logger.warning("无法注册中文字体 %s: %s", font_path, exc)
    return "Helvetica"


def _score_color(score: float) -> colors.Color:
    """根据 0-1 分数返回对应颜色。"""
    if score >= 0.8:
        return colors.HexColor("#16a34a")
    if score >= 0.6:
        return colors.HexColor("#3b82f6")
    if score >= 0.4:
        return colors.HexColor("#f59e0b")
    return colors.HexColor("#ef4444")


def _format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.0f}%"


def _chunk_text(text: str, max_length: int = 200) -> str:
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def generate_match_report_pdf(
    match_data: dict[str, Any],
    job_data: dict[str, Any] | None = None,
    profile_data: dict[str, Any] | None = None,
) -> bytes:
    """生成匹配报告 PDF 字节流。

    Args:
        match_data: 匹配结果数据，字段与 MatchResultOut 对齐。
        job_data: 岗位信息，用于展示岗位标题、公司、城市、薪资等。
        profile_data: 用户画像信息，可选。

    Returns:
        PDF 文件字节流。
    """
    font_name = _register_chinese_font()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCN",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#111827"),
        spaceAfter=8 * mm,
    )
    heading_style = ParagraphStyle(
        "HeadingCN",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=4 * mm,
        spaceBefore=6 * mm,
    )
    body_style = ParagraphStyle(
        "BodyCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
    )
    small_style = ParagraphStyle(
        "SmallCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#6b7280"),
    )
    score_style = ParagraphStyle(
        "ScoreCN",
        fontName=font_name,
        fontSize=48,
        leading=52,
        alignment=1,  # center
    )
    score_label_style = ParagraphStyle(
        "ScoreLabelCN",
        fontName=font_name,
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#6b7280"),
        alignment=1,
    )

    story: list[Any] = []

    # Header
    story.append(Paragraph("TalentMatch 匹配报告", title_style))
    story.append(
        Paragraph(
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            small_style,
        )
    )
    story.append(Spacer(1, 6 * mm))

    # Job info
    if job_data:
        story.append(Paragraph("岗位信息", heading_style))
        company = job_data.get("company") or {}
        job_title = Paragraph(str(job_data.get("title", "-")), body_style)
        company_name = Paragraph(str(company.get("name", "-")), body_style)
        city = Paragraph(str(job_data.get("city", "-")), body_style)
        salary = Paragraph(
            f"¥{job_data.get('salary_min', 0):,} - ¥{job_data.get('salary_max', 0):,}",
            body_style,
        )
        experience = Paragraph(str(job_data.get("experience_level", "-")), body_style)
        education = Paragraph(str(job_data.get("education_level", "-")), body_style)
        job_rows = [
            [Paragraph("岗位名称", body_style), job_title],
            [Paragraph("公司名称", body_style), company_name],
            [Paragraph("工作城市", body_style), city],
            [Paragraph("薪资范围", body_style), salary],
            [Paragraph("经验要求", body_style), experience],
            [Paragraph("学历要求", body_style), education],
        ]
        job_table = Table(job_rows, colWidths=[35 * mm, 115 * mm])
        job_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#374151")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(job_table)
        story.append(Spacer(1, 6 * mm))

    # Profile info (optional)
    if profile_data:
        story.append(Paragraph("用户画像", heading_style))
        skills = profile_data.get("skills", [])
        targets = profile_data.get("target_job_titles", [])
        profile_name = Paragraph(str(profile_data.get("name", "-")), body_style)
        profile_experience = Paragraph(
            str(profile_data.get("experience_level", "-")),
            body_style,
        )
        profile_skills = Paragraph(
            ", ".join(str(s) for s in skills) or "-",
            body_style,
        )
        profile_targets = Paragraph(
            ", ".join(str(t) for t in targets) or "-",
            body_style,
        )
        profile_rows = [
            [Paragraph("画像名称", body_style), profile_name],
            [Paragraph("经验等级", body_style), profile_experience],
            [Paragraph("技能", body_style), profile_skills],
            [Paragraph("目标岗位", body_style), profile_targets],
        ]
        profile_table = Table(profile_rows, colWidths=[35 * mm, 115 * mm])
        profile_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(profile_table)
        story.append(Spacer(1, 6 * mm))

    # Match score
    story.append(Paragraph("匹配评分", heading_style))
    match_score = float(match_data.get("match_score", 0.0))
    score_color = _score_color(match_score)
    score_paragraph = Paragraph(
        f'<font color="{score_color.hexval()}">{_format_percent(match_score)}</font>',
        score_style,
    )
    score_label = Paragraph("总体匹配分数", score_label_style)

    detail_data = [
        [
            score_paragraph,
            Paragraph(_format_percent(match_data.get("skill_score")), score_style),
            Paragraph(_format_percent(match_data.get("experience_match")), score_style),
            Paragraph(_format_percent(match_data.get("education_match")), score_style),
        ],
        [
            score_label,
            Paragraph("技能分数", score_label_style),
            Paragraph("经验匹配", score_label_style),
            Paragraph("学历匹配", score_label_style),
        ],
    ]
    score_table = Table(detail_data, colWidths=[37.5 * mm, 37.5 * mm, 37.5 * mm, 37.5 * mm])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(score_table)
    story.append(Spacer(1, 6 * mm))

    # Skill comparison
    story.append(Paragraph("技能对比", heading_style))
    matched = match_data.get("matched_skills", [])
    missing = match_data.get("missing_skills", [])
    transferable = match_data.get("transferable_skills", [])

    skill_rows = [
        [
            Paragraph(f"已匹配技能（{len(matched)} 项）", body_style),
            Paragraph(f"缺失技能（{len(missing)} 项）", body_style),
        ],
        [
            Paragraph(
                ", ".join(str(s) for s in matched) if matched else "无",
                body_style,
            ),
            Paragraph(
                ", ".join(str(s) for s in missing) if missing else "无",
                body_style,
            ),
        ],
    ]
    if transferable:
        skill_rows.append(
            [
                Paragraph("可迁移技能", body_style),
                Paragraph(", ".join(str(s) for s in transferable), body_style),
            ]
        )

    skill_table = Table(skill_rows, colWidths=[75 * mm, 75 * mm])
    skill_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(skill_table)
    story.append(Spacer(1, 6 * mm))

    # Analysis summary
    story.append(Paragraph("分析摘要", heading_style))
    summary = match_data.get("analysis_summary") or "暂无分析摘要"
    story.append(Paragraph(_chunk_text(summary, 800), body_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
