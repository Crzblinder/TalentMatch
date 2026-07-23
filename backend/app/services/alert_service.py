"""告警服务。

根据 Prometheus 指标评估告警规则，触发时记录结构化日志，
并支持通过邮件或 Webhook 发送通知。
"""

from __future__ import annotations

import json
import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any

import requests

from app.api.metrics import registry
from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """单个告警规则。"""

    name: str
    description: str
    threshold: float
    metric_name: str
    labels: dict[str, str] = field(default_factory=dict)
    value_getter: callable = field(default=lambda samples: 0.0)


@dataclass
class AlertEvent:
    """告警事件。"""

    rule: str
    severity: str
    value: float
    threshold: float
    message: str
    fired_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _collect_counter_rate(metric_name: str, total_label: str, failure_label: str) -> float:
    """从 Counter 指标计算失败率。"""
    total = 0.0
    failures = 0.0
    for sample in registry.collect():
        for s in sample.samples:
            if s.name == metric_name:
                labels = s.labels
                if all(labels.get(k) == v for k, v in {"status": total_label}.items()):
                    total += s.value
                if all(labels.get(k) == v for k, v in {"status": failure_label}.items()):
                    failures += s.value
    if total + failures == 0:
        return 0.0
    return failures / (total + failures)


def _collect_llm_failure_rate() -> float:
    """计算 LLM 调用失败率。"""
    return _collect_counter_rate("talentmatch_llm_call_total", "success", "failure")


def _collect_rss_fetch_failure_rate() -> float:
    """计算 RSS 采集失败率。"""
    return _collect_counter_rate("talentmatch_rss_fetch_total", "success", "failure")


def _collect_parse_failure_rate() -> float:
    """计算解析任务失败率。"""
    return _collect_counter_rate("talentmatch_parse_task_total", "success", "failure")


def get_alert_rules(settings: Settings | None = None) -> list[AlertRule]:
    """返回当前配置下的告警规则列表。"""
    if settings is None:
        settings = get_settings()
    return [
        AlertRule(
            name="llm_failure_rate_high",
            description="LLM 调用失败率超过阈值",
            threshold=settings.alert_llm_failure_rate_threshold,
            metric_name="talentmatch_llm_call_total",
            value_getter=_collect_llm_failure_rate,
        ),
        AlertRule(
            name="rss_fetch_failure_rate_high",
            description="RSS 采集失败率超过阈值",
            threshold=settings.alert_rss_fetch_failure_rate_threshold,
            metric_name="talentmatch_rss_fetch_total",
            value_getter=_collect_rss_fetch_failure_rate,
        ),
        AlertRule(
            name="parse_failure_rate_high",
            description="解析任务失败率超过阈值",
            threshold=settings.alert_parse_failure_rate_threshold,
            metric_name="talentmatch_parse_task_total",
            value_getter=_collect_parse_failure_rate,
        ),
    ]


def evaluate_alert_rules(settings: Settings | None = None) -> list[AlertEvent]:
    """评估所有告警规则并返回触发的事件。"""
    if settings is None:
        settings = get_settings()

    events: list[AlertEvent] = []
    if not settings.alert_enabled:
        return events

    for rule in get_alert_rules(settings):
        value = rule.value_getter()
        if value >= rule.threshold:
            event = AlertEvent(
                rule=rule.name,
                severity="warning",
                value=round(value, 4),
                threshold=rule.threshold,
                message=f"{rule.description}: 当前 {value:.2%}，阈值 {rule.threshold:.2%}",
                fired_at=_now_iso(),
            )
            events.append(event)
            _log_alert(event)
    return events


def _log_alert(event: AlertEvent) -> None:
    """记录结构化告警日志。"""
    logger.warning(
        json.dumps({
            "event": "alert_fired",
            "rule": event.rule,
            "severity": event.severity,
            "value": event.value,
            "threshold": event.threshold,
            "message": event.message,
            "fired_at": event.fired_at,
        }, ensure_ascii=False)
    )


def send_alert_notifications(
    events: list[AlertEvent],
    settings: Settings | None = None,
) -> dict[str, Any]:
    """发送告警通知，返回各通道结果。"""
    if settings is None:
        settings = get_settings()

    results = {"email": None, "webhook": None}
    if not events:
        return results

    if settings.alert_email_smtp_host and settings.alert_email_to:
        results["email"] = _send_email_alert(events, settings)

    if settings.alert_webhook_url:
        results["webhook"] = _send_webhook_alert(events, settings)

    return results


def _send_email_alert(events: list[AlertEvent], settings: Settings) -> dict[str, Any]:
    """通过 SMTP 发送邮件告警。"""
    subject = f"[TalentMatch] 告警触发 ({len(events)} 条)"
    body_lines = [
        (
            f"规则: {e.rule}\n严重级别: {e.severity}\n值: {e.value}\n"
            f"阈值: {e.threshold}\n消息: {e.message}\n时间: {e.fired_at}\n"
        )
        for e in events
    ]
    body = "\n---\n".join(body_lines)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.alert_email_smtp_user or "talentmatch@example.com"
    msg["To"] = settings.alert_email_to

    try:
        use_ssl = settings.alert_email_smtp_port == 465
        if use_ssl:
            server_cls = smtplib.SMTP_SSL
        else:
            server_cls = smtplib.SMTP

        with server_cls(
            settings.alert_email_smtp_host,
            settings.alert_email_smtp_port,
            timeout=10,
        ) as server:
            if settings.alert_email_smtp_user and settings.alert_email_smtp_password:
                if not use_ssl:
                    server.starttls()
                server.login(settings.alert_email_smtp_user, settings.alert_email_smtp_password)
            server.sendmail(
                msg["From"],
                [addr.strip() for addr in settings.alert_email_to.split(",") if addr.strip()],
                msg.as_string(),
            )
        return {"success": True, "channel": "email"}
    except Exception as exc:  # noqa: BLE001
        logger.warning("邮件告警发送失败: %s", exc)
        return {"success": False, "channel": "email", "error": str(exc)}


def _send_webhook_alert(events: list[AlertEvent], settings: Settings) -> dict[str, Any]:
    """通过 Webhook 发送告警。"""
    payload = {
        "source": "talentmatch",
        "alerts": [
            {
                "rule": e.rule,
                "severity": e.severity,
                "value": e.value,
                "threshold": e.threshold,
                "message": e.message,
                "fired_at": e.fired_at,
            }
            for e in events
        ],
    }
    try:
        response = requests.post(
            settings.alert_webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        return {"success": True, "channel": "webhook", "status_code": response.status_code}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Webhook 告警发送失败: %s", exc)
        return {"success": False, "channel": "webhook", "error": str(exc)}


def run_alert_evaluation(settings: Settings | None = None) -> dict[str, Any]:
    """运行一次完整的告警评估与通知。"""
    if settings is None:
        settings = get_settings()

    if not settings.alert_enabled:
        logger.info("告警功能未启用，跳过评估")
        return {"enabled": False, "events": [], "notifications": {}}

    events = evaluate_alert_rules(settings)
    notifications = send_alert_notifications(events, settings)
    return {
        "enabled": True,
        "events": [event.__dict__ for event in events],
        "notifications": notifications,
    }
