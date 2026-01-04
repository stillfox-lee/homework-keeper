"""
V1 版本图片上传与批次管理 API
使用 VLM（视觉语言模型）替代传统 OCR
"""
import json
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import HomeworkBatch, BatchImage, HomeworkItem, Subject
from backend.services.vlm_service import get_vlm_service
from backend.services.homework_service import get_homework_service
from backend.api.deps import get_current_child
from backend.schemas import (
    VLMUploadDraftResponse,
    DraftBatchInfo,
    BatchImageResponse,
    HomeworkItemResponse,
    HomeworkBatchResponse,
    VLMDraftConfirmRequest,
    VLMParsedHomeworkItem,
    ParsedHomeworkItem,
    VLMImageClassification,
)
from backend.config import settings

router = APIRouter(prefix="/api/v1/upload", tags=["upload-v1"])


def _batch_image_to_response(img: BatchImage) -> BatchImageResponse:
    """转换批次图片为响应格式"""
    response = BatchImageResponse.model_validate(img)
    response.file_path = f"/uploads/{img.file_path}"  # type: ignore
    return response


def _subject_response_dict(subject: Subject) -> dict:
    """科目转字典"""
    return {
        "id": subject.id,
        "name": subject.name,
        "color": subject.color,
        "sort_order": subject.sort_order,
    }


def _item_to_response(item: HomeworkItem, subject: Subject) -> HomeworkItemResponse:
    """作业项转响应"""
    return HomeworkItemResponse(
        id=item.id,
        batch_id=item.batch_id,
        source_image_id=item.source_image_id,
        subject=_subject_response_dict(subject),
        text=item.text,
        key_concept=item.key_concept,
        status=item.status,
        started_at=item.started_at,
        finished_at=item.finished_at,
        created_at=item.created_at,
    )


@router.post("/draft", response_model=VLMUploadDraftResponse)
async def upload_draft_batch_vlm(
    files: List[UploadFile],
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """
    上传图片，通过 VLM 解析创建 draft 批次

    流程：
    1. 保存所有图片
    2. 调用 VLM 一次性完成：
       - 图片分类（homework / reference）
       - 作业项提取
       - reference 关联
    3. 根据分类结果更新 BatchImage.image_type
    4. 返回完整解析结果
    """
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    homework_service = get_homework_service()
    vlm_service = get_vlm_service()

    # 创建 draft 批次
    batch = homework_service.create_draft_batch(db, child.id)

    # 处理每张图片
    uploaded_images = []
    image_paths = []

    for i, file in enumerate(files):
        # 验证文件类型
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            continue

        # 读取文件
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            continue

        # 保存图片
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = settings.UPLOAD_DIR / filename

        with open(file_path, "wb") as f:
            f.write(content)

        # 创建图片记录（image_type 先设为 homework，后续由 VLM 修正）
        batch_image = BatchImage(
            batch_id=batch.id,
            file_path=filename,
            file_name=file.filename,
            file_size=len(content),
            sort_order=i,
            image_type="homework",
            raw_ocr_text=None,
            ocr_status="pending",
            ocr_error=None,
        )
        db.add(batch_image)
        uploaded_images.append(batch_image)
        image_paths.append(str(file_path))

    db.flush()

    # 获取科目列表
    subjects = db.query(Subject).all()
    subject_dicts = [{"id": s.id, "name": s.name} for s in subjects]
    subject_map = {s.id: s for s in subjects}

    # 获取原始上传文件名列表，用于 VLM 显示和结果匹配
    original_filenames = [img.file_name for img in uploaded_images]

    # 调用 VLM 服务，传递原始文件名
    vlm_result = await vlm_service.parse_homework_images(
        image_paths=image_paths,
        subjects=subject_dicts,
        original_filenames=original_filenames
    )

    # 构建 VLM 解析结果
    parsed_result = None
    if vlm_result.success:
        # 更新图片分类
        image_map = {img.sort_order: img for img in uploaded_images}
        # 构建文件名到 sort_order 的映射
        file_name_to_order = {img.file_name: img.sort_order for img in uploaded_images}

        for file_name in vlm_result.homework_images:
            if file_name in file_name_to_order:
                idx = file_name_to_order[file_name]
                image_map[idx].image_type = "homework"
                # 更新 raw_ocr_text 为 JSON 格式
                image_map[idx].raw_ocr_text = json.dumps({"type": "homework"}, ensure_ascii=False)

        for file_name in vlm_result.reference_images:
            if file_name in file_name_to_order:
                idx = file_name_to_order[file_name]
                image_map[idx].image_type = "reference"
                image_map[idx].raw_ocr_text = json.dumps({"type": "reference"}, ensure_ascii=False)

        # 标记 OCR 状态为成功
        for img in uploaded_images:
            img.ocr_status = "success"

        # 构建 homework_images 和 reference_images 的 sort_order 列表
        homework_sort_orders = [
            file_name_to_order[name] for name in vlm_result.homework_images if name in file_name_to_order
        ]
        reference_sort_orders = [
            file_name_to_order[name] for name in vlm_result.reference_images if name in file_name_to_order
        ]

        # 构建文件名到 BatchImage 的映射（用于查找 source_image_id）
        file_name_to_image = {img.file_name: img for img in uploaded_images}

        # 转换作业项为 ParsedHomeworkItem
        parsed_items = []
        for item in vlm_result.homework_items:
            subject_id = item.get("subject_id")

            # 跳过未匹配科目的作业项（subject_id == -1）
            if subject_id == -1:
                continue

            # 查找科目
            subject = subject_map.get(subject_id)
            if subject:
                # 根据 homeworkFileName 查找 source_image_id
                homework_file_name = item.get("homeworkFileName")
                source_image = file_name_to_image.get(homework_file_name) if homework_file_name else None
                source_image_id = source_image.id if source_image else None

                parsed_items.append(ParsedHomeworkItem(
                    subject_id=subject.id,
                    subject_name=subject.name,
                    text=item.get("text", ""),
                    key_concept=None,
                    source_image_id=source_image_id
                ))

        # 转换原始 VLM 返回
        raw_items = [VLMParsedHomeworkItem(**item) for item in vlm_result.homework_items]

        from backend.schemas import VLMParseResult, VLMImageClassification
        parsed_result = VLMParseResult(
            success=True,
            classification=VLMImageClassification(
                homework_images=homework_sort_orders,
                reference_images=reference_sort_orders
            ),
            items=parsed_items,
            raw_items=raw_items,
            unmatched_subjects=vlm_result.new_subject_names,  # 未匹配的科目名
            error=None
        )

        # 保存 VLM 解析结果到批次（用于草稿恢复）
        batch.vlm_parse_result = json.dumps(parsed_result.model_dump(), ensure_ascii=False)
    else:
        # VLM 解析失败，保存错误信息
        from backend.schemas import VLMParseResult
        batch.vlm_parse_result = json.dumps(
            VLMParseResult(
                success=False,
                classification=None,
                items=[],
                raw_items=[],
                unmatched_subjects=[],
                error=vlm_result.error or "VLM 解析失败"
            ).model_dump(),
            ensure_ascii=False
        )

    db.commit()

    # 构建响应
    image_responses = [_batch_image_to_response(img) for img in uploaded_images]

    return VLMUploadDraftResponse(
        success=True,
        batch=DraftBatchInfo(
            id=batch.id,
            name=batch.name,
            status=batch.status,
            deadline_at=batch.deadline_at
        ),
        batch_id=batch.id,
        images=image_responses,
        parsed=parsed_result,
    )


@router.post("/{batch_id}/confirm", response_model=HomeworkBatchResponse)
async def confirm_draft_batch_vlm(
    batch_id: int,
    data: VLMDraftConfirmRequest,
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """
    确认 draft 批次，激活并保存作业项

    支持用户修改图片分类和作业项
    """
    # 验证批次所有权
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    if batch.status != "draft":
        raise HTTPException(status_code=400, detail="只能确认 draft 状态的批次")

    # 如果用户提供了分类更新，先应用
    if data.image_classification:
        images = db.query(BatchImage).filter(BatchImage.batch_id == batch_id).all()
        image_map = {img.sort_order: img for img in images}

        for idx in data.image_classification.homework_images:
            if idx in image_map:
                image_map[idx].image_type = "homework"

        for idx in data.image_classification.reference_images:
            if idx in image_map:
                image_map[idx].image_type = "reference"

        db.commit()

    # 获取科目
    subjects = db.query(Subject).all()
    subject_map = {s.id: s for s in subjects}

    # 创建作业项
    for item_data in data.items:
        # 更新 source_image 的 raw_ocr_text，存储 reference 关联
        source_image_id = item_data.source_image_id
        if source_image_id:
            # 从 raw_items 中查找是否有 reference
            # 这里需要前端传递 reference 关联信息
            pass

        item = HomeworkItem(
            batch_id=batch.id,
            subject_id=item_data.subject_id,
            text=item_data.text,
            key_concept=item_data.key_concept,
            source_image_id=item_data.source_image_id,
            status="todo",
        )
        db.add(item)

    # 设置截止时间
    if data.deadline_at:
        batch.deadline_at = data.deadline_at

    # 先保存作业项到数据库（此时批次仍是 draft）
    db.commit()

    # 先查询数据用于构建响应（确保在激活批次前构建响应成功）
    items = db.query(HomeworkItem).filter(HomeworkItem.batch_id == batch_id).all()
    images = db.query(BatchImage).filter(BatchImage.batch_id == batch_id).all()
    subjects = db.query(Subject).all()
    subject_map = {s.id: s for s in subjects}

    # 先构建响应，确保数据格式正确
    response = HomeworkBatchResponse(
        id=batch.id,
        child_id=batch.child_id,
        name=batch.name,
        status=batch.status,
        deadline_at=batch.deadline_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=[_item_to_response(item, subject_map[item.subject_id]) for item in items],
        images=[_batch_image_to_response(img) for img in images],
        vlm_parse_result=None
    )

    # 响应构建成功后，激活批次（draft → active）
    homework_service = get_homework_service()
    homework_service.activate_batch(db, batch_id)

    # 清空 VLM 解析结果（已确认，不再需要）
    batch.vlm_parse_result = None

    db.commit()
    db.refresh(batch)

    # 重新构建响应以反映最新的批次状态
    response = HomeworkBatchResponse(
        id=batch.id,
        child_id=batch.child_id,
        name=batch.name,
        status=batch.status,
        deadline_at=batch.deadline_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=[_item_to_response(item, subject_map[item.subject_id]) for item in items],
        images=[_batch_image_to_response(img) for img in images],
        vlm_parse_result=None
    )
    return response


@router.get("/{batch_id}/images", response_model=List[BatchImageResponse])
async def get_batch_images(
    batch_id: int, child=Depends(get_current_child), db: Session = Depends(get_db)
):
    """获取批次的图片列表"""
    # 验证批次所有权
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    images = (
        db.query(BatchImage)
        .filter(BatchImage.batch_id == batch_id)
        .order_by(BatchImage.sort_order)
        .all()
    )

    return [_batch_image_to_response(img) for img in images]


@router.patch("/{batch_id}/images/{image_id}/type")
async def update_image_type(
    batch_id: int,
    image_id: int,
    image_type: str = Form(...),
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """
    更新图片类型（homework ↔ reference）

    Args:
        batch_id: 批次ID
        image_id: 图片ID
        image_type: 新类型（homework 或 reference）

    Returns:
        更新后的图片
    """
    if image_type not in ["homework", "reference"]:
        raise HTTPException(status_code=400, detail="无效的图片类型")

    # 验证批次所有权
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 更新图片类型
    image = (
        db.query(BatchImage)
        .filter(BatchImage.id == image_id, BatchImage.batch_id == batch_id)
        .first()
    )

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    image.image_type = image_type
    db.commit()

    return _batch_image_to_response(image)


@router.delete("/{batch_id}/images/{image_id}")
async def delete_batch_image(
    batch_id: int,
    image_id: int,
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """
    删除批次图片

    Args:
        batch_id: 批次ID
        image_id: 图片ID

    Returns:
        删除成功消息
    """
    # 验证批次所有权
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 查询图片
    image = (
        db.query(BatchImage)
        .filter(BatchImage.id == image_id, BatchImage.batch_id == batch_id)
        .first()
    )

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 删除文件
    file_path = settings.UPLOAD_DIR / image.file_path
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            # 文件删除失败不影响数据库记录删除
            print(f"Warning: Failed to delete file {file_path}: {e}")

    # 删除关联的作业项（如果该图片是 source_image）
    related_items = (
        db.query(HomeworkItem)
        .filter(HomeworkItem.source_image_id == image_id)
        .all()
    )
    for item in related_items:
        db.delete(item)

    # 删除数据库记录
    db.delete(image)
    db.commit()

    return {"message": "图片已删除"}
