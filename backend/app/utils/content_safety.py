"""内容安全检测与数据脱敏工具。

对接阿里云内容安全（绿网）文本反垃圾接口，并提供手机号、身份证号等
基础脱敏能力。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import time
import uuid
from typing import Any
from urllib.parse import quote

import requests

from app.config import Settings

logger = logging.getLogger(__name__)

PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
ID_CARD_PATTERN = re.compile(r"\d{17}[\dXx]|\d{15}")

GREEN_API_PATH = "/v2/text/advanced"
DEFAULT_SERVICE = "comment_detection"


def _percent_encode(value: str) -> str:
    """阿里云 POP 签名专用 URL 编码（RFC3986，空格编码为 %20）。"""
    return quote(value, safe="").replace("+", "%20").replace("*", "%2A").replace("%7E", "~")


def _build_signature(
    method: str,
    access_key_secret: str,
    params: dict[str, str],
) -> str:
    """构造阿里云 HMAC-SHA1 签名。"""
    sorted_params = sorted(params.items())
    canonical_query = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted_params
    )
    string_to_sign = f"{method.upper()}&{_percent_encode('/')}&{_percent_encode(canonical_query)}"
    key = f"{access_key_secret}&".encode()
    signature = hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(signature).decode("utf-8")


def _call_green_api(
    text: str,
    settings: Settings,
) -> dict[str, Any]:
    """调用阿里云内容安全文本检测 API。"""
    endpoint = settings.content_safety_endpoint.rstrip("/")
    url = f"https://{endpoint}{GREEN_API_PATH}"

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    nonce = str(uuid.uuid4())

    service_parameters = json.dumps({"content": text}, ensure_ascii=False, separators=(",", ":"))

    query_params: dict[str, str] = {
        "AccessKeyId": settings.alibaba_cloud_access_key_id,
        "Action": "TextModeration",
        "Format": "JSON",
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": nonce,
        "SignatureVersion": "1.0",
        "Timestamp": timestamp,
        "Version": "2022-03-02",
        "Service": DEFAULT_SERVICE,
        "ServiceParameters": service_parameters,
    }

    signature = _build_signature(
        "POST",
        settings.alibaba_cloud_access_key_secret,
        query_params,
    )
    query_params["Signature"] = signature

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    body = {
        "service": DEFAULT_SERVICE,
        "serviceParameters": {"content": text},
    }

    logger.info("调用阿里云内容安全 API 进行文本检测，文本长度: %d", len(text))
    response = requests.post(
        url,
        params=query_params,
        headers=headers,
        json=body,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _parse_safety_result(api_result: dict[str, Any]) -> dict[str, Any]:
    """解析阿里云内容安全返回结果。"""
    code = api_result.get("code")
    if code != 200:
        logger.warning("内容安全 API 返回非成功状态码: %s, msg: %s", code, api_result.get("msg"))
        return {"safe": True, "labels": [], "suggestion": "pass"}

    data = api_result.get("data", [])
    if not isinstance(data, list) or not data:
        logger.warning("内容安全 API 返回数据为空")
        return {"safe": True, "labels": [], "suggestion": "pass"}

    results = data[0].get("results", []) if isinstance(data[0], dict) else []
    labels: list[str] = []
    suggestions: set[str] = set()

    for result in results:
        if not isinstance(result, dict):
            continue
        label = result.get("label")
        if label:
            labels.append(str(label))
        suggestion = result.get("suggestion")
        if suggestion:
            suggestions.add(str(suggestion).lower())

    if "block" in suggestions:
        logger.warning("检测到违规内容，labels: %s", labels)
        return {"safe": False, "labels": labels, "suggestion": "block"}
    if "review" in suggestions:
        logger.info("内容安全建议人工复核，labels: %s", labels)
        return {"safe": True, "labels": labels, "suggestion": "review"}

    logger.info("文本内容安全检测通过")
    return {"safe": True, "labels": labels, "suggestion": "pass"}


def check_text_safety(text: str, settings: Settings) -> dict[str, Any]:
    """检测文本是否包含违规内容。

    Args:
        text: 待检测文本
        settings: 应用配置

    Returns:
        包含 safe、labels、suggestion 的字典；未开启或调用失败时默认放行
    """
    if not settings.enable_content_safety:
        logger.info("内容安全总开关未开启，跳过文本检测")
        return {"safe": True, "labels": [], "suggestion": "pass"}

    if not text or not isinstance(text, str):
        logger.info("待检测文本为空或非字符串，跳过文本检测")
        return {"safe": True, "labels": [], "suggestion": "pass"}

    if not settings.alibaba_cloud_access_key_id or not settings.alibaba_cloud_access_key_secret:
        logger.warning("内容安全已开启但阿里云 AccessKey 未配置，默认放行")
        return {"safe": True, "labels": [], "suggestion": "pass"}

    try:
        api_result = _call_green_api(text, settings)
        return _parse_safety_result(api_result)
    except requests.exceptions.RequestException as exc:
        logger.warning("内容安全 API 请求失败，默认放行: %s", exc)
    except Exception as exc:
        logger.warning("内容安全检测异常，默认放行: %s", exc)

    return {"safe": True, "labels": [], "suggestion": "pass"}


def mask_sensitive_text(text: str) -> str:
    """对文本中的手机号和身份证号进行脱敏。

    - 手机号：保留前 3 位和后 4 位，中间替换为 ****
    - 身份证号：保留前 6 位和后 4 位，中间替换为 **********
    """
    if not isinstance(text, str):
        return text

    def _mask_phone(match: re.Match[str]) -> str:
        value = match.group(0)
        return f"{value[:3]}****{value[-4:]}"

    def _mask_id_card(match: re.Match[str]) -> str:
        value = match.group(0)
        return f"{value[:6]}**********{value[-4:]}"

    # 先脱敏身份证号，避免手机号正则误匹配身份证号中的连续数字
    masked = ID_CARD_PATTERN.sub(_mask_id_card, text)
    masked = PHONE_PATTERN.sub(_mask_phone, masked)
    return masked


def mask_resume_data(resume_data: dict[str, Any]) -> dict[str, Any]:
    """递归遍历简历结构化数据，对字符串值进行脱敏。"""
    if isinstance(resume_data, dict):
        return {k: mask_resume_data(v) for k, v in resume_data.items()}
    if isinstance(resume_data, list):
        return [mask_resume_data(item) for item in resume_data]
    if isinstance(resume_data, tuple):
        return tuple(mask_resume_data(item) for item in resume_data)
    if isinstance(resume_data, set):
        return {mask_resume_data(item) for item in resume_data}
    if isinstance(resume_data, str):
        return mask_sensitive_text(resume_data)
    return resume_data
