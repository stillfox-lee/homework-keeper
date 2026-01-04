"""
作业解析服务 - 业务逻辑层
负责科目映射、新科目检测、结果组装
"""

from typing import List, Dict, Optional, NamedTuple, Set
from pathlib import Path

from loguru import logger

from backend.services.vlm_service import VLMService, VLMOutput, HomeworkItem


class VLMResult(NamedTuple):
    """VLM 解析结果"""

    success: bool
    homework_images: List[str]
    reference_images: List[str]
    homework_items: List[Dict]
    new_subject_names: List[str] = []
    error: Optional[str] = None


class HomeworkParserService:
    """作业解析服务 - 业务逻辑层"""

    def __init__(self):
        self._vlm_service: Optional[VLMService] = None

    def _get_vlm_service(self) -> VLMService:
        """获取 VLM 服务实例"""
        if self._vlm_service is None:
            from backend.services.vlm_service import get_vlm_service

            self._vlm_service = get_vlm_service()
        return self._vlm_service

    def _match_subject_id(
        self,
        subject_name: str,
        subjects: List[Dict],
    ) -> tuple[int, bool, str]:
        """
        匹配科目名称到 ID

        Args:
            subject_name: VLM 返回的科目名称
            subjects: 现有科目列表 [{"id": 1, "name": "数学"}, ...]

        Returns:
            (subject_id, is_new, matched_name)
            - subject_id: 匹配到的科目 ID，-1 表示新科目
            - is_new: 是否为新科目
            - matched_name: 最终使用的科目名称
        """
        # 1. 精确匹配
        for s in subjects:
            if s["name"] == subject_name:
                return s["id"], False, s["name"]

        # 2. 模糊匹配（包含关系）
        for s in subjects:
            if subject_name in s["name"] or s["name"] in subject_name:
                return s["id"], False, s["name"]

        # 3. 新科目
        return -1, True, subject_name

    def _map_vlm_output_to_result(
        self,
        vlm_output: VLMOutput,
        subjects: List[Dict],
        image_paths: List[str],
        original_filenames: List[str] = None,
    ) -> VLMResult:
        """
        将 VLMOutput 映射为 VLMResult

        Args:
            vlm_output: LLM 返回的原始输出
            subjects: 现有科目列表
            image_paths: 所有图片路径列表
            original_filenames: 原始上传文件名列表（与 image_paths 一一对应）

        Returns:
            VLMResult 包含科目 ID 映射和新科目信息
        """
        homework_items = []
        new_subject_names: Set[str] = set()

        # 使用原始文件名列表计算 reference_images
        all_image_names = original_filenames if original_filenames else [Path(p).name for p in image_paths]
        # reference_images = 所有图片 - homework图片
        reference_images = list(set(all_image_names) - set(vlm_output.homeworkFileName))

        for item in vlm_output.homework_items:
            subject_name = item.subject.strip()
            subject_id, is_new, matched_name = self._match_subject_id(
                subject_name, subjects
            )

            if is_new:
                new_subject_names.add(subject_name)
                logger.info(f"[Parser] 检测到新科目: {subject_name}")

            homework_items.append(
                {
                    "subject": matched_name,
                    "text": item.text,
                    "homeworkFileName": item.homeworkFileName,
                    "subject_id": subject_id,  # -1 表示新科目
                }
            )

        result = VLMResult(
            success=True,
            homework_images=vlm_output.homeworkFileName,
            reference_images=reference_images,
            homework_items=homework_items,
            new_subject_names=list(new_subject_names),
            error=None,
        )

        if new_subject_names:
            logger.info(
                f"[Parser] 解析完成，发现新科目: {list(new_subject_names)}",
                extra={
                    "new_subjects": list(new_subject_names),
                    "total_items": len(homework_items),
                },
            )
        else:
            logger.info(f"[Parser] 解析完成，共 {len(homework_items)} 个作业项")

        return result

    async def parse_homework_images(
        self,
        image_paths: List[str],
        subjects: List[Dict],
        original_filenames: List[str] = None,
    ) -> VLMResult:
        """
        解析作业图片 - 完整流程

        这是原有的 parse_homework_images 方法，迁移到业务逻辑层

        Args:
            image_paths: 图片路径列表（实际存储路径）
            subjects: 科目列表 [{"id": 1, "name": "数学"}, ...]
            original_filenames: 原始上传文件名列表（与 image_paths 一一对应）

        Returns:
            VLMResult 包含图片分类和作业项（带科目 ID）
        """
        if not image_paths:
            logger.warning("[Parser] 没有提供图片")
            return VLMResult(
                success=False,
                homework_images=[],
                reference_images=[],
                homework_items=[],
                error="没有提供图片",
            )

        if original_filenames and len(original_filenames) != len(image_paths):
            raise ValueError("original_filenames 长度必须与 image_paths 相同")

        logger.info(
            f"[Parser] 开始解析作业图片，现有科目: {[s['name'] for s in subjects]}"
        )

        # 提取科目名称
        subject_names = [s["name"] for s in subjects]

        # 调用核心 LLM 层，传递原始文件名用于显示
        vlm_service = self._get_vlm_service()
        try:
            vlm_output = await vlm_service.call_llm(image_paths, subject_names, original_filenames)
        except Exception as e:
            logger.error(f"[Parser] VLM 调用失败: {e}")
            return VLMResult(
                success=False,
                homework_images=[],
                reference_images=[],
                homework_items=[],
                error=f"VLM 调用失败: {str(e)}",
            )

        # 映射结果，传递原始文件名用于计算 reference_images
        return self._map_vlm_output_to_result(vlm_output, subjects, image_paths, original_filenames)

    async def call_llm_only(
        self,
        image_paths: List[str],
        subject_names: List[str],
    ) -> VLMOutput:
        """
        仅调用 LLM 的便捷方法，供测试脚本使用

        Args:
            image_paths: 图片路径列表
            subject_names: 科目名称列表

        Returns:
            VLMOutput Pydantic 对象
        """
        vlm_service = self._get_vlm_service()
        return await vlm_service.call_llm(image_paths, subject_names)


# 全局单例
_parser_service: Optional[HomeworkParserService] = None


def get_homework_parser_service() -> HomeworkParserService:
    """获取作业解析服务单例"""
    global _parser_service
    if _parser_service is None:
        _parser_service = HomeworkParserService()
    return _parser_service
