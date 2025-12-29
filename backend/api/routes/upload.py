"""
图片上传与批次管理 API
"""
from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from pathlib import Path

from backend.database import get_db
from backend.models import (
    HomeworkBatch, BatchImage, HomeworkItem, Subject
)
from backend.services.ocr_service import get_ocr_service
from backend.services.llm_service import get_llm_service
from backend.services.homework_service import get_homework_service
from backend.api.deps import get_current_child
from backend.schemas import (
    UploadDraftResponse,
    DraftBatchInfo,
    BatchImageResponse,
    HomeworkItemResponse,
    HomeworkBatchResponse,
    DraftConfirmRequest,
    HomeworkItemCreate,
    ParsedHomeworkItem,
)
from backend.config import settings

router = APIRouter(prefix="/api/upload", tags=["upload"])


def _batch_image_to_response(img: BatchImage) -> BatchImageResponse:
    """转换批次图片为响应格式"""
    return BatchImageResponse(
        id=img.id,
        batch_id=img.batch_id,
        file_path=f"/uploads/{img.file_path}",
        file_name=img.file_name,
        file_size=img.file_size,
        sort_order=img.sort_order,
        image_type=img.image_type,
        raw_ocr_text=img.raw_ocr_text,
        created_at=img.created_at
    )


def _subject_response_dict(subject: Subject) -> dict:
    """科目转字典"""
    return {
        "id": subject.id,
        "name": subject.name,
        "color": subject.color,
        "sort_order": subject.sort_order
    }


@router.post("/draft", response_model=UploadDraftResponse)
async def upload_draft_batch(
    files: List[UploadFile],
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """
    上传图片，创建 draft 状态的批次

    流程：
    1. 保存所有图片
    2. 对每张图片进行 OCR 识别
    3. 创建 draft 批次
    4. 返回批次信息和识别结果
    """
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    homework_service = get_homework_service()
    ocr_service = get_ocr_service()

    # 创建 draft 批次
    batch = homework_service.create_draft_batch(db, child.id)

    # 处理每张图片
    uploaded_images = []
    all_ocr_text = []

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

        # OCR 识别
        ocr_text = ocr_service.recognize_image(str(file_path))
        if ocr_text:
            all_ocr_text.append(ocr_text)

        # 创建图片记录
        batch_image = BatchImage(
            batch_id=batch.id,
            file_path=filename,
            file_name=file.filename,
            file_size=len(content),
            sort_order=i,
            image_type='homework',  # 默认为作业清单类型
            raw_ocr_text=ocr_text
        )
        db.add(batch_image)
        uploaded_images.append(batch_image)

    db.flush()

    # 构建 response
    image_responses = [_batch_image_to_response(img) for img in uploaded_images]

    # 合并 OCR 文本
    merged_ocr_text = "\n\n".join(all_ocr_text) if all_ocr_text else None

    db.commit()

    return UploadDraftResponse(
        success=True,
        data={"batch_id": batch.id, "name": batch.name},
        batch=DraftBatchInfo(id=batch.id, name=batch.name, status=batch.status),
        batch_id=batch.id,
        images=image_responses,
        ocr_text=merged_ocr_text
    )


@router.post("/parse", response_model=List[ParsedHomeworkItem])
async def parse_ocr_text(
    batch_id: int = Form(...),
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """
    解析 OCR 文本为作业项（LLM/规则）

    Args:
        batch_id: 批次ID

    Returns:
        解析出的作业项列表
    """
    # 验证批次所有权
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 获取所有 homework 类型的图片文本
    images = db.query(BatchImage).filter(
        BatchImage.batch_id == batch_id,
        BatchImage.image_type == 'homework'
    ).all()

    # 合并 OCR 文本
    ocr_texts = [img.raw_ocr_text for img in images if img.raw_ocr_text]
    merged_text = "\n".join(ocr_texts)

    if not merged_text:
        return []

    # 获取科目列表
    subjects = db.query(Subject).all()
    subject_dicts = [{"id": s.id, "name": s.name} for s in subjects]

    # 使用 LLM 服务解析
    llm_service = get_llm_service()
    parsed_items = llm_service.parse_homework_text(merged_text, subject_dicts)

    # 转换为响应格式
    return [
        ParsedHomeworkItem(
            subject_id=item['subject_id'],
            subject_name=item['subject_name'],
            text=item['text'],
            key_concept=item['key_concept']
        )
        for item in parsed_items
    ]


@router.post("/{batch_id}/confirm", response_model=HomeworkBatchResponse)
async def confirm_draft_batch(
    batch_id: int,
    data: DraftConfirmRequest,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """
    确认 draft 批次，激活并保存作业项

    Args:
        batch_id: 批次ID
        data: 包含作业项列表和截止时间

    Returns:
        激活后的批次
    """
    # 验证批次所有权
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    if batch.status != 'draft':
        raise HTTPException(status_code=400, detail="只能确认 draft 状态的批次")

    # 获取科目
    subjects = db.query(Subject).all()
    subject_map = {s.id: s for s in subjects}

    # 创建作业项
    for item_data in data.items:
        item = HomeworkItem(
            batch_id=batch.id,
            subject_id=item_data.subject_id,
            text=item_data.text,
            key_concept=item_data.key_concept,
            source_image_id=item_data.source_image_id,
            status='todo'
        )
        db.add(item)

    # 设置截止时间
    if data.deadline_at:
        batch.deadline_at = data.deadline_at

    # 激活批次
    homework_service = get_homework_service()
    homework_service.activate_batch(db, batch_id)

    db.commit()
    db.refresh(batch)

    # 构建响应
    items = db.query(HomeworkItem).filter(HomeworkItem.batch_id == batch_id).all()
    images = db.query(BatchImage).filter(BatchImage.batch_id == batch_id).all()

    return HomeworkBatchResponse(
        id=batch.id,
        child_id=batch.child_id,
        name=batch.name,
        status=batch.status,
        deadline_at=batch.deadline_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=[
            HomeworkItemResponse(
                id=item.id,
                batch_id=item.batch_id,
                source_image_id=item.source_image_id,
                subject=_subject_response_dict(subject_map[item.subject_id]),
                text=item.text,
                key_concept=item.key_concept,
                status=item.status,
                started_at=item.started_at,
                finished_at=item.finished_at,
                created_at=item.created_at
            )
            for item in items
        ],
        images=[_batch_image_to_response(img) for img in images]
    )


@router.get("/{batch_id}/images", response_model=List[BatchImageResponse])
async def get_batch_images(
    batch_id: int,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """获取批次的图片列表"""
    # 验证批次所有权
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    images = db.query(BatchImage).filter(
        BatchImage.batch_id == batch_id
    ).order_by(BatchImage.sort_order).all()

    return [_batch_image_to_response(img) for img in images]


@router.patch("/{batch_id}/images/{image_id}/type")
async def update_image_type(
    batch_id: int,
    image_id: int,
    image_type: str = Form(...),
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
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
    if image_type not in ['homework', 'reference']:
        raise HTTPException(status_code=400, detail="无效的图片类型")

    # 验证批次所有权
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 更新图片类型
    image = db.query(BatchImage).filter(
        BatchImage.id == image_id,
        BatchImage.batch_id == batch_id
    ).first()

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    image.image_type = image_type
    db.commit()

    return _batch_image_to_response(image)
