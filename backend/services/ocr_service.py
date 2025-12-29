"""
OCR 识别服务 - 只负责文字识别，不做解析
"""
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
from typing import List


class OCRService:
    """OCR 识别服务"""

    def __init__(self):
        """初始化 PaddleOCR"""
        self.ocr = None

    def _ensure_initialized(self):
        """延迟初始化 OCR"""
        if self.ocr is None:
            try:
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch'
                )
            except Exception as e:
                print(f"OCR 初始化失败: {e}")
                self.ocr = None

    def recognize_image(self, image_path: str) -> str:
        """
        识别单张图片，返回文本

        Args:
            image_path: 图片路径

        Returns:
            识别出的文本，多行用换行符连接
        """
        self._ensure_initialized()

        if self.ocr is None:
            return ""

        try:
            # 读取图片
            img = Image.open(image_path)
            img_array = np.array(img)

            # OCR 识别
            result = self.ocr.ocr(img_array, cls=True)

            # 提取文本
            return self._extract_text(result)

        except Exception as e:
            print(f"OCR 识别失败: {e}")
            return ""

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
            text = self.recognize_image(path)
            if text:
                texts.append(f"--- 图片 {i+1} ---\n{text}")

        return "\n\n".join(texts)

    def _extract_text(self, ocr_result) -> str:
        """从 OCR 结果提取文本"""
        if not ocr_result or not ocr_result[0]:
            return ""

        texts = []
        for line in ocr_result[0]:
            if line and line[1] and line[1][0]:
                texts.append(line[1][0])

        return '\n'.join(texts)


# 全局单例
_ocr_service = None


def get_ocr_service() -> OCRService:
    """获取 OCR 服务单例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
