#!/usr/bin/env python3
"""LLM Eval 评估脚本：评估简历/JD 解析 Agent 的准确率、幻觉率与 JSON 成功率。

运行方式（无需真实付费 API Key）：
    cd backend
    python -m eval.run_eval

默认使用规则引擎降级输出；如需使用真实 LLM，可设置 OPENAI_API_KEY。
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 确保 backend 目录在导入路径中
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# 优先使用规则引擎，不依赖付费 API Key
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("USE_LOCAL_LLM", "false")

from app.agents.jd_parser import JDParser  # noqa: E402
from app.agents.resume_parser import ResumeParser  # noqa: E402


@dataclass
class SampleResult:
    """单个样本的评估结果。"""

    sample_id: str
    passed: bool
    field_scores: dict[str, float]
    hallucination_score: float
    json_success: bool
    latency_ms: int
    details: list[str] = field(default_factory=list)


@dataclass
class EvalReport:
    """评估报告。"""

    task: str
    total: int
    passed: int
    failed: int
    accuracy: float
    hallucination_rate: float
    json_success_rate: float
    avg_latency_ms: float
    per_sample: list[SampleResult]
    summary: dict[str, Any] = field(default_factory=dict)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    """加载 JSONL 数据集，跳过空行。"""
    samples: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))
    return samples


def _normalize_text(value: Any) -> str:
    """将任意值归一化为字符串，用于模糊匹配。"""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ",".join(str(v).strip() for v in value if v)
    return str(value).strip()


def _list_overlap_score(actual: list[str], expected: list[str]) -> float:
    """计算两个字符串列表的重叠得分（基于期望项的命中比例）。"""
    if not expected:
        return 1.0 if not actual else 0.0
    actual_lower = {_normalize_text(v).lower() for v in actual if _normalize_text(v)}
    expected_lower = {_normalize_text(v).lower() for v in expected if _normalize_text(v)}
    if not expected_lower:
        return 1.0 if not actual_lower else 0.0
    matched = sum(1 for e in expected_lower if any(e in a or a in e for a in actual_lower))
    return matched / len(expected_lower)


def _scalar_match(actual: Any, expected: Any) -> float:
    """计算标量字段的匹配得分，支持包含关系。"""
    actual_str = _normalize_text(actual).lower()
    expected_str = _normalize_text(expected).lower()
    if not expected_str:
        return 1.0 if not actual_str else 0.5
    if actual_str == expected_str:
        return 1.0
    if expected_str in actual_str or actual_str in expected_str:
        return 0.8
    return 0.0


def _evaluate_resume(sample: dict[str, Any]) -> SampleResult:
    """评估单个简历样本。"""
    expected = sample.get("expected", {})
    text = sample["text"]

    start = time.perf_counter()
    parser = ResumeParser()
    result = parser.parse_resume(text)
    latency_ms = int((time.perf_counter() - start) * 1000)

    json_success = isinstance(result, dict) and not result.get("simulated")

    field_scores: dict[str, float] = {}
    details: list[str] = []

    # 基本信息字段
    basic_expected = expected.get("basic_info", {})
    basic_actual = result.get("basic_info", {})
    basic_fields = ["name", "phone", "email", "gender"]
    basic_scores = []
    for f in basic_fields:
        score = _scalar_match(basic_actual.get(f), basic_expected.get(f))
        basic_scores.append(score)
        if score < 1.0:
            details.append(
                f"basic_info.{f}: 期望={basic_expected.get(f)!r}, 实际={basic_actual.get(f)!r}"
            )
    field_scores["basic_info"] = sum(basic_scores) / len(basic_scores) if basic_scores else 1.0

    # 技能列表
    skills_score = _list_overlap_score(result.get("skills", []), expected.get("skills", []))
    field_scores["skills"] = skills_score
    if skills_score < 1.0:
        details.append(
            f"skills: 期望={expected.get('skills', [])}, 实际={result.get('skills', [])}"
        )

    # 教育经历（按学校数量与学位匹配）
    expected_edu = expected.get("education", [])
    actual_edu = result.get("education", [])
    if expected_edu:
        edu_scores = []
        for exp in expected_edu:
            best = 0.0
            for act in actual_edu:
                school_score = _scalar_match(act.get("school"), exp.get("school"))
                major_score = _scalar_match(act.get("major"), exp.get("major"))
                degree_score = _scalar_match(act.get("degree"), exp.get("degree"))
                combined = (school_score + major_score + degree_score) / 3
                if combined > best:
                    best = combined
            edu_scores.append(best)
        field_scores["education"] = sum(edu_scores) / len(edu_scores)
        if field_scores["education"] < 1.0:
            details.append(f"education: 期望={expected_edu}, 实际={actual_edu}")
    else:
        field_scores["education"] = 1.0

    # 工作经历（按公司+职位匹配）
    expected_work = expected.get("work_experience", [])
    actual_work = result.get("work_experience", [])
    if expected_work:
        work_scores = []
        for exp in expected_work:
            best = 0.0
            for act in actual_work:
                company_score = _scalar_match(act.get("company"), exp.get("company"))
                position_score = _scalar_match(act.get("position"), exp.get("position"))
                combined = (company_score + position_score) / 2
                if combined > best:
                    best = combined
            work_scores.append(best)
        field_scores["work_experience"] = sum(work_scores) / len(work_scores)
        if field_scores["work_experience"] < 1.0:
            details.append(f"work_experience: 期望={expected_work}, 实际={actual_work}")
    else:
        field_scores["work_experience"] = 1.0

    # 获奖经历
    awards_score = _list_overlap_score(result.get("awards", []), expected.get("awards", []))
    field_scores["awards"] = awards_score
    if awards_score < 1.0:
        details.append(
            f"awards: 期望={expected.get('awards', [])}, "
            f"实际={result.get('awards', [])}"
        )

    # 自我评价
    self_eval_score = _scalar_match(
        result.get("self_evaluation", ""), expected.get("self_evaluation", "")
    )
    field_scores["self_evaluation"] = self_eval_score
    if self_eval_score < 1.0:
        details.append(
            f"self_evaluation: 期望={expected.get('self_evaluation', '')!r}, "
            f"实际={result.get('self_evaluation', '')!r}"
        )

    # 求职意向
    ji_expected = expected.get("job_intention", {})
    ji_actual = result.get("job_intention", {})
    ji_scores = []
    for f in ["expected_position", "expected_city"]:
        score = _scalar_match(ji_actual.get(f), ji_expected.get(f))
        ji_scores.append(score)
        if score < 1.0:
            details.append(
                f"job_intention.{f}: 期望={ji_expected.get(f)!r}, "
                f"实际={ji_actual.get(f)!r}"
            )
    field_scores["job_intention"] = sum(ji_scores) / len(ji_scores) if ji_scores else 1.0

    # 幻觉：输出中出现了期望/输入中都没有的技能
    hallucination_score = _calculate_hallucination(result, expected, text)

    overall_accuracy = sum(field_scores.values()) / len(field_scores) if field_scores else 1.0
    passed = overall_accuracy >= 0.7 and not result.get("simulated")

    return SampleResult(
        sample_id=sample["id"],
        passed=passed,
        field_scores=field_scores,
        hallucination_score=hallucination_score,
        json_success=json_success,
        latency_ms=latency_ms,
        details=details,
    )


def _evaluate_jd(sample: dict[str, Any]) -> SampleResult:
    """评估单个 JD 样本。"""
    expected = sample.get("expected", {})
    text = sample["text"]

    start = time.perf_counter()
    parser = JDParser()
    result = parser.parse_jd(text)
    latency_ms = int((time.perf_counter() - start) * 1000)

    json_success = isinstance(result, dict) and not result.get("simulated")

    field_scores: dict[str, float] = {}
    details: list[str] = []

    # 岗位名称
    title_score = _scalar_match(result.get("title", ""), expected.get("title", ""))
    field_scores["title"] = title_score
    if title_score < 1.0:
        details.append(f"title: 期望={expected.get('title')!r}, 实际={result.get('title')!r}")

    # 技能列表
    skills_score = _list_overlap_score(
        result.get("required_skills", []), expected.get("required_skills", [])
    )
    field_scores["required_skills"] = skills_score
    if skills_score < 1.0:
        details.append(
            f"required_skills: 期望={expected.get('required_skills', [])}, "
            f"实际={result.get('required_skills', [])}"
        )

    # 经验要求
    exp_score = _scalar_match(
        result.get("experience_level", ""), expected.get("experience_level", "")
    )
    field_scores["experience_level"] = exp_score
    if exp_score < 1.0:
        details.append(
            f"experience_level: 期望={expected.get('experience_level')!r}, "
            f"实际={result.get('experience_level')!r}"
        )

    # 学历要求
    edu_score = _scalar_match(
        result.get("education_level", ""), expected.get("education_level", "")
    )
    field_scores["education_level"] = edu_score
    if edu_score < 1.0:
        details.append(
            f"education_level: 期望={expected.get('education_level')!r}, "
            f"实际={result.get('education_level')!r}"
        )

    # 隐性需求
    implicit_score = _list_overlap_score(
        result.get("implicit_needs", []), expected.get("implicit_needs", [])
    )
    field_scores["implicit_needs"] = implicit_score
    if implicit_score < 1.0:
        details.append(
            f"implicit_needs: 期望={expected.get('implicit_needs', [])}, "
            f"实际={result.get('implicit_needs', [])}"
        )

    hallucination_score = _calculate_hallucination(result, expected, text)

    overall_accuracy = sum(field_scores.values()) / len(field_scores) if field_scores else 1.0
    passed = overall_accuracy >= 0.6 and not result.get("simulated")

    return SampleResult(
        sample_id=sample["id"],
        passed=passed,
        field_scores=field_scores,
        hallucination_score=hallucination_score,
        json_success=json_success,
        latency_ms=latency_ms,
        details=details,
    )


def _calculate_hallucination(
    result: dict[str, Any], expected: dict[str, Any], source_text: str
) -> float:
    """简单幻觉检测：输出技能是否出现在原文或期望中。

    返回幻觉比例：出现幻觉的技能数 / 输出技能总数。
    """
    result_skills: set[str] = set()
    for key in ("skills", "required_skills"):
        if key in result and isinstance(result[key], list):
            result_skills.update(_normalize_text(s).lower() for s in result[key] if s)

    expected_skills: set[str] = set()
    for key in ("skills", "required_skills"):
        if key in expected and isinstance(expected[key], list):
            expected_skills.update(_normalize_text(s).lower() for s in expected[key] if s)

    source_text_lower = source_text.lower()

    if not result_skills:
        return 0.0

    hallucinated = 0
    for skill in result_skills:
        if skill in expected_skills:
            continue
        if skill in source_text_lower:
            continue
        # 允许部分匹配，如 "fastapi" 出现在 "FastAPI" 中
        tokens = source_text_lower.replace(",", " ").replace("、", " ").split()
        if any(skill in token for token in tokens):
            continue
        hallucinated += 1

    return hallucinated / len(result_skills)


def _run_task(task_name: str, samples: list[dict[str, Any]], evaluator: Any) -> EvalReport:
    """运行一项评估任务并生成报告。"""
    per_sample: list[SampleResult] = []
    for sample in samples:
        per_sample.append(evaluator(sample))

    total = len(per_sample)
    passed = sum(1 for r in per_sample if r.passed)
    accuracies = [sum(r.field_scores.values()) / len(r.field_scores) for r in per_sample]
    hallucinations = [r.hallucination_score for r in per_sample]
    json_successes = [r.json_success for r in per_sample]
    latencies = [r.latency_ms for r in per_sample]

    return EvalReport(
        task=task_name,
        total=total,
        passed=passed,
        failed=total - passed,
        accuracy=sum(accuracies) / len(accuracies) if accuracies else 0.0,
        hallucination_rate=sum(hallucinations) / len(hallucinations) if hallucinations else 0.0,
        json_success_rate=sum(json_successes) / len(json_successes) if json_successes else 0.0,
        avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        per_sample=per_sample,
    )


def _report_to_dict(report: EvalReport) -> dict[str, Any]:
    """将报告对象转为可序列化的字典。"""
    return {
        "task": report.task,
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "accuracy": round(report.accuracy, 4),
        "hallucination_rate": round(report.hallucination_rate, 4),
        "json_success_rate": round(report.json_success_rate, 4),
        "avg_latency_ms": round(report.avg_latency_ms, 2),
        "samples": [
            {
                "sample_id": r.sample_id,
                "passed": r.passed,
                "field_scores": {k: round(v, 4) for k, v in r.field_scores.items()},
                "hallucination_score": round(r.hallucination_score, 4),
                "json_success": r.json_success,
                "latency_ms": r.latency_ms,
                "details": r.details,
            }
            for r in report.per_sample
        ],
    }


def _write_markdown_report(
    reports: list[EvalReport], output_path: Path, run_at: str
) -> None:
    """生成 Markdown 评估报告。"""
    lines: list[str] = [
        "# TalentMatch LLM Eval 评估报告",
        "",
        f"生成时间：{run_at}",
        "",
        "## 概述",
        "",
        f"- 评估任务数：{len(reports)}",
        f"- 总样本数：{sum(r.total for r in reports)}",
        "",
        "## 汇总指标",
        "",
        "| 任务 | 样本数 | 通过 | 失败 | 准确率 | 幻觉率 | JSON 成功率 | 平均耗时(ms) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in reports:
        lines.append(
            f"| {r.task} | {r.total} | {r.passed} | {r.failed} | "
            f"{r.accuracy:.2%} | {r.hallucination_rate:.2%} | "
            f"{r.json_success_rate:.2%} | {r.avg_latency_ms:.2f} |"
        )

    for r in reports:
        lines.extend([
            "",
            f"## {r.task}",
            "",
            f"- 准确率：{r.accuracy:.2%}",
            f"- 幻觉率：{r.hallucination_rate:.2%}",
            f"- JSON 结构化成功率：{r.json_success_rate:.2%}",
            f"- 平均耗时：{r.avg_latency_ms:.2f} ms",
            "",
            "### 样本明细",
            "",
            "| 样本ID | 结果 | 准确率 | 幻觉率 | JSON成功 | 耗时(ms) |",
            "| --- | --- | --- | --- | --- | --- |",
        ])
        for sample in r.per_sample:
            sample_acc = sum(sample.field_scores.values()) / len(sample.field_scores)
            status = "通过" if sample.passed else "失败"
            lines.append(
                f"| {sample.sample_id} | {status} | {sample_acc:.2%} | "
                f"{sample.hallucination_score:.2%} | {sample.json_success} | {sample.latency_ms} |"
            )
            for detail in sample.details:
                lines.append(f"- {detail}")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    """主入口：加载数据集、执行评估、输出报告。"""
    eval_dir = Path(__file__).resolve().parent
    data_dir = eval_dir / "data"
    reports_dir = eval_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    resume_samples = _load_jsonl(data_dir / "resume_parse_samples.jsonl")
    jd_samples = _load_jsonl(data_dir / "jd_parse_samples.jsonl")

    print(f"Loaded {len(resume_samples)} resume samples, {len(jd_samples)} jd samples")

    resume_report = _run_task("resume_parse", resume_samples, _evaluate_resume)
    jd_report = _run_task("jd_parse", jd_samples, _evaluate_jd)

    reports = [resume_report, jd_report]

    run_at = time.strftime("%Y-%m-%d %H:%M:%S")
    json_output = {
        "run_at": run_at,
        "backend": "rule_engine" if not os.environ.get("OPENAI_API_KEY") else "llm",
        "tasks": [_report_to_dict(r) for r in reports],
    }

    json_path = reports_dir / "eval_report.json"
    json_path.write_text(json.dumps(json_output, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = reports_dir / "eval_report.md"
    _write_markdown_report(reports, md_path, run_at)

    print("\nEval report written to:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    print()
    print("Summary:")
    for r in reports:
        print(
            f"  {r.task}: accuracy={r.accuracy:.2%}, "
            f"hallucination={r.hallucination_rate:.2%}, "
            f"json_success={r.json_success_rate:.2%}, "
            f"avg_latency={r.avg_latency_ms:.2f}ms"
        )

    # 任意任务准确率低于 0.5 则返回非零，便于 CI 中断
    if any(r.accuracy < 0.5 for r in reports):
        print("\nAccuracy below threshold (0.5).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
