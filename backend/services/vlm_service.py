"""
VLM (Vision Language Model) 服务
使用智谱 GLM-4V-Flash 进行作业图片解析
"""

import asyncio
import base64
import imghdr
import json
import random
import re
from typing import List, Dict, Optional
from pathlib import Path

from pydantic import BaseModel, Field
from zhipuai import ZhipuAI
from loguru import logger
from backend.config import settings


# ==================== 工具函数 ====================


def generate_random_color() -> str:
    """生成随机 HEX 颜色（避免过浅）"""
    while True:
        color = f"#{random.randint(0, 0xFFFFFF):06X}"
        # 检查亮度，避免太浅（使用感知亮度公式）
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        if 50 < brightness < 200:  # 避免太暗或太亮
            return color


# ==================== VLM 输出格式定义 ====================


class VLMHomeworkItem(BaseModel):
    """VLM 解析的作业项"""

    subject: str = Field(..., description="科目名称")
    text: str = Field(..., description="作业文本内容")
    homeworkFileName: str = Field(..., description="作业图片文件名")
    has_reference: bool = Field(..., description="是否有参考资料")
    referenceFileName: str = Field(
        default="", description="参考资料文件名，无则为空字符串"
    )


class VLMOutput(BaseModel):
    """VLM 输出格式"""

    referenceFileName: List[str] = Field(
        ..., description="reference 类型图片的文件名列表，如 ['picxxx', 'img222']"
    )
    homeworkFileName: List[str] = Field(
        ..., description="homework 类型图片的文件名列表，如 ['image0', 'image1']"
    )
    homework_items: List[VLMHomeworkItem] = Field(..., description="作业项目列表")


# ==================== VLM 服务 ====================


class VLMService:
    """VLM 解析服务"""

    def __init__(self):
        self._client: Optional[ZhipuAI] = None

    def _ensure_client(self) -> ZhipuAI:
        """延迟初始化客户端"""
        if self._client is None:
            if not settings.ZHIPU_API_KEY:
                raise ValueError("ZHIPU_API_KEY 未配置")
            self._client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)
        return self._client

    def _image_to_base64(self, image_path: str) -> str:
        """将图片转换为 base64 data URL 格式"""

        with open(image_path, "rb") as f:
            image_data = f.read()

        # 检测图片类型
        img_type = imghdr.what(None, h=image_data) or "jpeg"
        mime_type = f"image/{img_type}"

        # 编码为 base64
        base64_str = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{base64_str}"

    def _build_prompt(
        self, subject_names: List[str], ordered_image_names: List[str]
    ) -> str:
        """构建 VLM Prompt

        Args:
            subject_names: 科目名称列表（纯字符串）
            ordered_image_names: 图片文件名列表（按顺序）
        """
        subjects_str = "、".join(subject_names)

        # 使用 Pydantic 模型生成 JSON Schema
        schema = VLMOutput.model_json_schema()
        json_schema = json.dumps(schema, ensure_ascii=False, indent=2)

        # 使用模型生成示例
        example = VLMOutput(
            referenceFileName=["image1"],
            homeworkFileName=["pic1", "h1"],
            homework_items=[
                VLMHomeworkItem(
                    subject="数学",
                    text="完成练习册第10页",
                    homeworkFileName="pic1",
                    has_reference=False,
                    referenceFileName="",
                ),
                VLMHomeworkItem(
                    subject="数学",
                    text="完成课本第20页练习题",
                    homeworkFileName="pic1",
                    has_reference=True,
                    referenceFileName="image1",
                ),
                VLMHomeworkItem(
                    subject="语文",
                    text="背诵古诗",
                    homeworkFileName="h1",
                    has_reference=False,
                    referenceFileName="",
                ),
            ],
        )
        json_example = example.model_dump_json(ensure_ascii=False, indent=2)

        return f"""你的任务是帮助学生从教师提供的一组图片列表中提取作业相关的信息。
图片信息说明：
- 图片分为两类：
    1. 作业清单照片。类型定义为 homework，这种图片是黑板板书的照片，包含老师布置的作业内容。
    2. 参考资料照片。类型定义为 reference。这种图片是与作业清单相关的参考资料。


你需要按照下面的要求处理图片：
1. 先识别图片中的文字内容，然后为图片分类为两类：homework 或者 reference。
2. 对每张 homework 的图片，识别其中的内容，提取为 HomeworkItem 信息。注意理解作业图片内容，将相关的参考资料图片与之关联(referenceFileName)。
3. 构建数据对象，输出 JSON 格式数据。

关于 HomeworkItem 拆解的注意事项：
- HomeworkItem 是作业独立单元，每个 HomeworkItem 都是可以独立完成的作业任务。
- 需要注意，有时候图片中可能同一个 HomeworkItem 会出现换行的情况，你需要根据语义的相关性来判断是否为同一个 HomeworkItem。
- 你应该尽可能将一张 homework 图片中的多个作业任务拆解为多个 HomeworkItem。
- HomeWorkItem.homeworkFileName 必须是这个作业来源的图片文件名。
- 一张 reference 图片，可以对应到一个 HomeworkItem，需要基于 reference 图片的内容来判断应该关联到哪个 HomeworkItem。

现有科目列表：{subjects_str}

**科目选择规则**：
1. 优先使用现有科目列表中的科目（支持语义匹配，如"数学科"对应"数学"，"英语作业"对应"英语"）
2. 如果现有科目列表中没有匹配的科目，可以根据作业内容自行判断并创建新的科目名称（如"物理"、"化学"、"生物"、"地理"、"历史"等）

JSON Schema：

```json
{json_schema}
```

输出示例：

```json
{json_example}
```

作业图片说明：
你得到的一组图片中，按照顺序依次文件名为：{", ".join(ordered_image_names)}。你必须使用这些文件名填充 JSON中的相关字段。

注意：只输出 JSON，不要添加任何其他说明文字。"""

    def _safe_parse_json(self, text: str) -> Optional[Dict]:
        """安全解析 JSON，处理常见格式问题"""
        # 去除前后空白
        text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 markdown 代码块中的 JSON
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取花括号内容（整个 JSON）
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                json_str = match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return None

    async def call_llm(
        self, image_paths: List[str], subject_names: List[str]
    ) -> VLMOutput:
        """
        核心方法：调用 LLM API 并返回解析结果

        Args:
            image_paths: 图片路径列表
            subject_names: 科目名称列表（纯字符串）

        Returns:
            VLMOutput Pydantic 对象

        Raises:
            ValueError: 图片为空或 API 调用失败
        """
        if not image_paths:
            raise ValueError("没有提供图片")

        logger.info(
            "[VLM] 开始解析作业图片",
            extra={
                "image_count": len(image_paths),
                "subjects": subject_names,
            },
        )

        client = self._ensure_client()

        # 提取图片文件名（不包含路径，只保留文件名）
        image_names = [Path(p).name for p in image_paths]
        logger.debug(f"image_names: {image_names}")

        # 构建消息内容
        content = [
            {"type": "text", "text": self._build_prompt(subject_names, image_names)}
        ]
        logger.debug(f"Prompt 内容:\n{content[0]['text']}")

        # 添加图片
        for i, path in enumerate(image_paths):
            base64_img = self._image_to_base64(path)
            content.append({"type": "image_url", "image_url": {"url": base64_img}})

        # 调用 API，带重试
        max_retries = settings.VLM_MAX_RETRIES
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"[VLM] 调用 API (尝试 {attempt + 1}/{max_retries})")
                response = client.chat.completions.create(
                    model=settings.VLM_MODEL,
                    messages=[{"role": "user", "content": content}],
                    thinking={"type": "enabled"},
                )

                # 获取响应文本
                if not response.choices:
                    raise ValueError("VLM 未返回结果")

                message = response.choices[0].message
                result_text = message.content or ""

                # 打印思考内容（如果有）
                if hasattr(message, "reasoning_content") and message.reasoning_content:
                    logger.debug(f"[VLM] 思考内容:\n{message.reasoning_content}")
                # 打印完整响应用于调试
                # logger.debug(f"[VLM] 完整响应: {response.model_dump()}")

                # 解析 JSON
                parsed = self._safe_parse_json(result_text)
                if not parsed:
                    raise ValueError(f"无法解析 VLM 返回的 JSON: {result_text[:200]}")

                # 验证并转换为 Pydantic 对象
                result = VLMOutput.model_validate(parsed)

                logger.info(
                    "[VLM] 解析成功",
                    extra={
                        "homework_images": len(result.homeworkFileName),
                        "reference_images": len(result.referenceFileName),
                        "homework_items": len(result.homework_items),
                    },
                )

                return result

            except ValueError:
                raise
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"[VLM] API 调用异常 (尝试 {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    # 指数退避
                    await asyncio.sleep(2**attempt)
                    continue
                else:
                    logger.error(f"[VLM] API 调用失败，已达最大重试次数: {last_error}")
                    raise ValueError(f"VLM 调用失败: {last_error}")

    async def parse_homework_images(
        self, image_paths: List[str], subjects: List[Dict]
    ) -> "VLMResult":
        """
        解析作业图片 - 委托给业务逻辑层

        此方法保持向后兼容，内部委托给 HomeworkParserService

        Args:
            image_paths: 图片路径列表
            subjects: 科目列表 [{"id": 1, "name": "数学"}, ...]

        Returns:
            VLMResult 包含图片分类和作业项
        """
        from backend.services.homework_parser_service import (
            get_homework_parser_service,
        )

        parser = get_homework_parser_service()
        return await parser.parse_homework_images(image_paths, subjects)


# 全局单例
_vlm_service: Optional[VLMService] = None


def get_vlm_service() -> VLMService:
    """获取 VLM 服务单例"""
    global _vlm_service
    if _vlm_service is None:
        _vlm_service = VLMService()
    return _vlm_service
