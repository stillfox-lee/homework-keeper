"""
OCR 识别服务 - 只负责文字识别，不做解析
"""
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
from typing import List, NamedTuple


class OCRResult(NamedTuple):
    """OCR 识别结果"""
    success: bool
    text: str
    error: str | None = None
    # 详细信息（用于调试）
    lines: List[str] | None = None  # 识别到的每一行
    scores: List[float] | None = None  # 每行的置信度


class OCRService:
    """OCR 识别服务"""

    def __init__(self):
        """初始化 PaddleOCR"""
        self.ocr = None

    def _ensure_initialized(self):
        """延迟初始化 OCR"""
        if self.ocr is None:
            try:
                self.ocr = PaddleOCR(lang='ch')
            except Exception as e:
                print(f"OCR 初始化失败: {e}")
                self.ocr = None

    def recognize_image(self, image_path: str, debug: bool = False) -> OCRResult:
        """
        识别单张图片，返回结果

        Args:
            image_path: 图片路径
            debug: 是否返回详细信息（每行文本和置信度）

        Returns:
            OCRResult 包含成功状态、文本和错误信息
        """
        self._ensure_initialized()

        if self.ocr is None:
            return OCRResult(
                success=False,
                text="",
                error="OCR 服务未初始化"
            )

        try:
            # 读取图片
            img = Image.open(image_path)
            img_array = np.array(img)

            # OCR 识别 - 使用新 API
            result = self.ocr.predict(img_array)

            # 提取文本
            extracted = self._extract_text(result, debug)

            if not extracted['text']:
                return OCRResult(
                    success=False,
                    text="",
                    error="未识别到任何文本"
                )

            return OCRResult(
                success=True,
                text=extracted['text'],
                lines=extracted.get('lines'),
                scores=extracted.get('scores')
            )

        except Exception as e:
            return OCRResult(
                success=False,
                text="",
                error=str(e)
            )

    def recognize_images(self, image_paths: List[str]) -> str:
        """
        识别多张图片，返回合并后的文本

        Args:
            image_paths: 图片路径列表

        Returns:
            合并后的文本，不同图片用分隔符连接
        """
        texts = []
        for i, path in enumerate(image_paths):
            result = self.recognize_image(path)
            if result.success and result.text:
                texts.append(f"--- 图片 {i+1} ---\n{result.text}")

        return "\n\n".join(texts)

    def _extract_text(self, ocr_result, debug: bool = False) -> dict:
        """
        从 OCR 结果提取文本

        Args:
            ocr_result: PaddleOCR.predict() 返回结果
            debug: 是否返回详细信息

        Returns:
            dict 包含 text（合并文本）, lines（每行）, scores（置信度）
        """
        result = {
            'text': '',
            'lines': None,
            'scores': None
        }

        if not ocr_result or not isinstance(ocr_result, list) or len(ocr_result) == 0:
            return result

        # 新版 PaddleOCR 返回 list，第一个元素是 OCRResult (dict-like)
        first = ocr_result[0]
        texts = first.get('rec_texts', [])
        scores = first.get('rec_scores', [])

        if texts:
            result['text'] = '\n'.join(texts)
            if debug:
                result['lines'] = texts
                result['scores'] = scores

        return result


# 全局单例
_ocr_service = None


def get_ocr_service() -> OCRService:
    """获取 OCR 服务单例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
