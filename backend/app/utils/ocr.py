"""本地 OCR 工具：图片转文本。

优先使用 rapidocr-onnxruntime（纯 Python，支持中英，无需额外安装 Tesseract）。
未安装时给出清晰提示，由调用方决定是否降级到云端多模态 LLM。
"""

from __future__ import annotations

import io
import logging
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)


def _get_ocr_engine() -> Any | None:
    """延迟导入 rapidocr，未安装时返回 None。"""
    try:
        from rapidocr_onnxruntime import RapidOCR

        return RapidOCR()
    except Exception as exc:  # pragma: no cover - 依赖可选
        logger.warning("rapidocr_onnxruntime 不可用: %s", exc)
        return None


def _preprocess_image(file_bytes: bytes, ext: str) -> bytes:
    """将图片统一转换为 RGB JPEG，提升 OCR 兼容性。"""
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            # 处理透明通道、CMYK 等模式
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGBA")
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # 限制最大边长，避免超大图片导致内存/性能问题
            max_size = 4096
            width, height = img.size
            if max(width, height) > max_size:
                ratio = max_size / max(width, height)
                img = img.resize(
                    (int(width * ratio), int(height * ratio)),
                    Image.Resampling.LANCZOS,
                )

            out = io.BytesIO()
            img.save(out, format="JPEG", quality=95)
            return out.getvalue()
    except Exception as exc:
        logger.warning("图片预处理失败，使用原图: %s", exc)
        return file_bytes


def extract_text_from_image(file_bytes: bytes, ext: str | None = None) -> str:
    """使用本地 OCR 从图片中提取文本。

    Args:
        file_bytes: 图片二进制数据。
        ext: 文件扩展名（如 png/jpg），仅用于日志，不影响实际解码。

    Returns:
        识别出的文本，按行拼接。

    Raises:
        RuntimeError: 未安装 rapidocr 且无法初始化 OCR 引擎。
    """
    engine = _get_ocr_engine()
    if engine is None:
        raise RuntimeError(
            "本地 OCR 不可用。请安装 rapidocr-onnxruntime："
            "pip install rapidocr-onnxruntime>=1.2.0"
        )

    processed = _preprocess_image(file_bytes, ext or "")
    logger.info("开始本地 OCR 识别，原始大小 %d bytes", len(file_bytes))

    try:
        result, _ = engine(processed)
    except Exception as exc:
        logger.exception("本地 OCR 识别失败")
        raise RuntimeError(f"本地 OCR 识别失败: {exc}") from exc

    if not result:
        logger.info("本地 OCR 未识别到文本")
        return ""

    # rapidocr 返回格式：[[[box], text, score], ...]
    texts: list[str] = []
    for item in result:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            text = str(item[1]).strip()
            if text:
                texts.append(text)
        elif isinstance(item, str):
            text = item.strip()
            if text:
                texts.append(text)

    logger.info("本地 OCR 识别完成，共 %d 行文本", len(texts))
    return "\n".join(texts)
