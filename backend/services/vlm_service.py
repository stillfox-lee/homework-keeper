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


class HomeworkItem(BaseModel):
    """从 homework 图片中提取的作业项"""

    subject: str = Field(..., description="科目名称")
    text: str = Field(..., description="作业文本内容")
    homeworkFileName: str = Field(..., description="homeworkList图片文件名")


class VLMOutput(BaseModel):
    """VLM 输出格式"""

    homeworkFileName: List[str] = Field(
        ..., description="homeworkList 类型图片的文件名列表，如 ['image0', 'image1']"
    )
    homework_items: List[HomeworkItem] = Field(..., description="作业清单列表")


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
            homeworkFileName=["pic1", "h1"],
            homework_items=[
                HomeworkItem(
                    subject="数学",
                    text="完成练习册第10页",
                    homeworkFileName="pic1",
                ),
                HomeworkItem(
                    subject="数学",
                    text="完成课本第20页练习题",
                    homeworkFileName="pic1",
                ),
                HomeworkItem(
                    subject="语文",
                    text="背诵古诗",
                    homeworkFileName="h1",
                ),
            ],
        )
        json_example = example.model_dump_json(ensure_ascii=False, indent=2)

        return f"""你的任务是帮助学生从教师提供的一组图片列表中提取作业相关的信息。


你需要按照下面的要求处理图片：
1. 找到作业任务图片，具体规则如下：
    - 如果图片内容是非常清楚的作业任务，则分类为 homeworkList。
    - 典型的 homeworkList 图片内容如：“语文：1.xxx 2.xxx 数学：1.xxx 2.xxx”
2. 对每张 homeworkList 的图片，识别其中的内容，提取为 HomeworkItem 信息。具体规则如下：
    - HomeworkItem 是作业独立单元，每个 HomeworkItem 都是可以独立完成的作业任务。
    - homeworkList 图片中可能同一个 HomeworkItem 会出现换行的情况，你需要根据语义的相关性来判断是否为同一个 HomeworkItem。
    - 你应该尽可能将一张 homeworkList 图片中的多个作业任务拆解为多个 HomeworkItem。
    - HomeWorkItem.text 中必须包含图片中的完整文字内容。
    - HomeWorkItem.homeworkFileName 必须是这个作业来源的 homeworkList 图片文件名。
3. 构建数据对象，输出 JSON 格式数据。


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

    # TODO: test case:
    # 多张 HomeworkList 的图片试试看能不能解析

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
        self, image_paths: List[str], subject_names: List[str], display_filenames: List[str] = None
    ) -> VLMOutput:
        """
        核心方法：调用 LLM API 并返回解析结果

        Args:
            image_paths: 图片路径列表（实际存储路径）
            subject_names: 科目名称列表（纯字符串）
            display_filenames: 传递给 VLM 的显示文件名列表（原始上传文件名），默认使用 image_paths 的文件名

        Returns:
            VLMOutput Pydantic 对象

        Raises:
            ValueError: 图片为空或 API 调用失败
        """
        if not image_paths:
            raise ValueError("没有提供图片")

        if display_filenames and len(display_filenames) != len(image_paths):
            raise ValueError("display_filenames 长度必须与 image_paths 相同")

        logger.info(
            "[VLM] 开始解析作业图片",
            extra={
                "image_count": len(image_paths),
                "subjects": subject_names,
            },
        )

        client = self._ensure_client()

        # 使用显示文件名（原始上传文件名），如果没有提供则从路径提取
        image_names = display_filenames if display_filenames else [Path(p).name for p in image_paths]
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
        self, image_paths: List[str], subjects: List[Dict], original_filenames: List[str] = None
    ) -> "VLMResult":
        """
        解析作业图片 - 委托给业务逻辑层

        此方法保持向后兼容，内部委托给 HomeworkParserService

        Args:
            image_paths: 图片路径列表
            subjects: 科目列表 [{"id": 1, "name": "数学"}, ...]
            original_filenames: 原始上传文件名列表（与 image_paths 一一对应）

        Returns:
            VLMResult 包含图片分类和作业项
        """
        from backend.services.homework_parser_service import (
            get_homework_parser_service,
        )

        parser = get_homework_parser_service()
        return await parser.parse_homework_images(image_paths, subjects, original_filenames)


# 全局单例
_vlm_service: Optional[VLMService] = None


def get_vlm_service() -> VLMService:
    """获取 VLM 服务单例"""
    global _vlm_service
    if _vlm_service is None:
        _vlm_service = VLMService()
    return _vlm_service
