"""
作业批次管理 API
"""
import json

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models import HomeworkBatch, HomeworkItem, BatchImage, Subject
from backend.services.homework_service import get_homework_service
from backend.api.deps import get_current_child
from backend.schemas import (
    HomeworkBatchResponse,
    HomeworkItemResponse,
    BatchImageResponse,
    HomeworkItemCreate,
    HomeworkItemUpdate,
    HomeworkItemStatusUpdate,
    BatchStatusUpdate,
    BatchUpdate,
    HomeworkItemUpdateOrCreate,
)

router = APIRouter(prefix="/api/batches", tags=["batches"])


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


def _image_to_response(img: BatchImage) -> BatchImageResponse:
    """图片转响应"""
    response = BatchImageResponse.model_validate(img)
    response.file_path = f"/uploads/{img.file_path}"  # type: ignore
    return response


def _batch_to_response(
    batch: HomeworkBatch,
    items: Optional[List[HomeworkItem]] = None,
    subjects: Optional[dict] = None
) -> HomeworkBatchResponse:
    """批次转响应（不包含 vlm_parse_result）"""
    response_items = []
    if items and subjects:
        response_items = [_item_to_response(item, subjects[item.subject_id]) for item in items]

    return HomeworkBatchResponse(
        id=batch.id,
        child_id=batch.child_id,
        name=batch.name,
        status=batch.status,
        deadline_at=batch.deadline_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=response_items,
        images=[],
        vlm_parse_result=None  # 批次列表不返回解析结果
    )


@router.get("", response_model=List[HomeworkBatchResponse])
async def get_batches(
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """获取批次列表（包含 items 用于显示进度）"""
    query = db.query(HomeworkBatch).filter(HomeworkBatch.child_id == child.id)

    if status:
        query = query.filter(HomeworkBatch.status == status)

    query = query.order_by(HomeworkBatch.created_at.desc())

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    batches = query.all()

    # 加载所有科目和作业项
    subjects = {s.id: s for s in db.query(Subject).all()}
    all_items = db.query(HomeworkItem).filter(
        HomeworkItem.batch_id.in_([b.id for b in batches])
    ).all()

    # 按批次分组 items
    items_by_batch = {}
    for item in all_items:
        if item.batch_id not in items_by_batch:
            items_by_batch[item.batch_id] = []
        items_by_batch[item.batch_id].append(item)

    return [
        _batch_to_response(b, items_by_batch.get(b.id), subjects)
        for b in batches
    ]


@router.get("/current", response_model=Optional[HomeworkBatchResponse])
async def get_current_batch(
    child=Depends(get_current_child), db: Session = Depends(get_db)
):
    """获取当前 active 批次"""
    homework_service = get_homework_service()
    batch = homework_service.get_active_batch(db, child.id)

    if not batch:
        return None

    # 加载作业项
    items = db.query(HomeworkItem).filter(HomeworkItem.batch_id == batch.id).all()
    subjects = {s.id: s for s in db.query(Subject).all()}

    response = _batch_to_response(batch)
    response.items = [
        _item_to_response(item, subjects[item.subject_id]) for item in items
    ]

    return response


@router.get("/{batch_id}", response_model=HomeworkBatchResponse)
async def get_batch(
    batch_id: int, child=Depends(get_current_child), db: Session = Depends(get_db)
):
    """获取批次详情"""
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 加载作业项和图片
    items = db.query(HomeworkItem).filter(HomeworkItem.batch_id == batch.id).all()
    images = db.query(BatchImage).filter(BatchImage.batch_id == batch.id).all()
    subjects = {s.id: s for s in db.query(Subject).all()}

    # 手动构造响应，避免 vlm_parse_result 类型冲突
    response = HomeworkBatchResponse(
        id=batch.id,
        child_id=batch.child_id,
        name=batch.name,
        status=batch.status,
        deadline_at=batch.deadline_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=[_item_to_response(item, subjects[item.subject_id]) for item in items],
        images=[_image_to_response(img) for img in images],
        vlm_parse_result=None  # 先设为 None
    )

    # draft 状态时返回 VLM 解析结果（用于草稿恢复）
    if batch.status == "draft" and batch.vlm_parse_result:
        try:
            response.vlm_parse_result = json.loads(batch.vlm_parse_result)
        except (json.JSONDecodeError, TypeError):
            response.vlm_parse_result = None

    return response


@router.get("/{batch_id}/items", response_model=List[HomeworkItemResponse])
async def get_batch_items(
    batch_id: int,
    status: Optional[str] = None,
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """获取批次的作业项列表"""
    # 验证批次所有权
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    query = db.query(HomeworkItem).filter(HomeworkItem.batch_id == batch_id)

    if status:
        query = query.filter(HomeworkItem.status == status)

    items = query.order_by(HomeworkItem.created_at).all()
    subjects = {s.id: s for s in db.query(Subject).all()}

    return [_item_to_response(item, subjects[item.subject_id]) for item in items]


@router.post("/{batch_id}/items", response_model=HomeworkItemResponse)
async def create_item(
    batch_id: int,
    data: HomeworkItemCreate,
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """向批次添加作业项"""
    # 验证批次所有权
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 验证科目
    subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="科目不存在")

    item = HomeworkItem(
        batch_id=batch_id,
        subject_id=data.subject_id,
        text=data.text,
        key_concept=data.key_concept,
        source_image_id=data.source_image_id,
        status="todo",
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return _item_to_response(item, subject)


@router.patch("/{batch_id}/status")
async def update_batch_status(
    batch_id: int,
    data: BatchStatusUpdate,
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """更新批次状态"""
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    if data.status not in ["draft", "active", "completed"]:
        raise HTTPException(status_code=400, detail="无效的状态")

    if data.status == "active":
        homework_service = get_homework_service()
        homework_service.activate_batch(db, batch_id)
    elif data.status == "completed":
        batch.status = "completed"
        batch.completed_at = datetime.now()
    else:
        batch.status = data.status

    db.commit()
    db.refresh(batch)

    return {"success": True, "data": _batch_to_response(batch)}


@router.delete("/{batch_id}")
async def delete_batch(
    batch_id: int, child=Depends(get_current_child), db: Session = Depends(get_db)
):
    """删除批次"""
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 删除关联的图片文件
    images = db.query(BatchImage).filter(BatchImage.batch_id == batch_id).all()
    for img in images:
        import os

        file_path = f"data/uploads/{img.file_path}"
        if os.path.exists(file_path):
            os.remove(file_path)

    # 删除数据库中的 BatchImage 记录
    for img in images:
        db.delete(img)

    # 删除数据库记录（级联删除会处理 items）
    db.delete(batch)
    db.commit()

    return {"success": True, "message": "批次已删除"}


@router.post("/{batch_id}/complete")
async def complete_batch(
    batch_id: int,
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """确认完成批次"""
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    if batch.status != "active":
        raise HTTPException(status_code=400, detail="只能完成进行中的批次")

    # 检查是否所有作业都已完成
    homework_service = get_homework_service()
    if not homework_service.check_batch_completion(db, batch.id):
        raise HTTPException(status_code=400, detail="还有作业未完成")

    batch.status = "completed"
    batch.completed_at = datetime.now()
    db.commit()

    return {"success": True}


@router.put("/{batch_id}", response_model=HomeworkBatchResponse)
async def update_batch(
    batch_id: int,
    data: BatchUpdate,
    child=Depends(get_current_child),
    db: Session = Depends(get_db),
):
    """更新批次信息（名称、截止时间、作业项）

    作业项采用完全替换策略：
    - 有 id 的项：更新
    - 无 id 的项：新建
    - 原有项不在新列表中：删除
    """
    # 验证批次所有权
    batch = (
        db.query(HomeworkBatch)
        .filter(HomeworkBatch.id == batch_id, HomeworkBatch.child_id == child.id)
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 更新基本信息
    if data.name is not None:
        batch.name = data.name
    if data.deadline_at is not None:
        batch.deadline_at = data.deadline_at

    # 更新作业项（完全替换）
    if data.items is not None:
        # 获取现有作业项
        existing_items = db.query(HomeworkItem).filter(
            HomeworkItem.batch_id == batch_id
        ).all()
        existing_item_ids = {item.id for item in existing_items}

        # 前端发送的作业项 ID 集合
        request_item_ids = {
            item.id for item in data.items if item.id is not None
        }

        # 删除不在新列表中的作业项
        items_to_delete = existing_item_ids - request_item_ids
        if items_to_delete:
            db.query(HomeworkItem).filter(
                HomeworkItem.id.in_(items_to_delete)
            ).delete(synchronize_session=False)

        # 获取所有科目
        subjects = {s.id: s for s in db.query(Subject).all()}

        # 处理新列表中的作业项
        for item_data in data.items:
            if item_data.id:
                # 更新现有作业项
                item = next((i for i in existing_items if i.id == item_data.id), None)
                if item:
                    if item_data.subject_id != item.subject_id:
                        if item_data.subject_id not in subjects:
                            raise HTTPException(status_code=404, detail=f"科目 {item_data.subject_id} 不存在")
                        item.subject_id = item_data.subject_id
                    if item_data.text is not None:
                        item.text = item_data.text
                    if item_data.key_concept is not None:
                        item.key_concept = item_data.key_concept
                    if item_data.source_image_id is not None:
                        item.source_image_id = item_data.source_image_id
            else:
                # 创建新作业项
                if item_data.subject_id not in subjects:
                    raise HTTPException(status_code=404, detail=f"科目 {item_data.subject_id} 不存在")

                new_item = HomeworkItem(
                    batch_id=batch_id,
                    subject_id=item_data.subject_id,
                    text=item_data.text,
                    key_concept=item_data.key_concept,
                    source_image_id=item_data.source_image_id,
                    status="todo",
                )
                db.add(new_item)

    # 更新时间戳
    batch.updated_at = datetime.now()
    db.commit()
    db.refresh(batch)

    # 重新加载并返回响应
    items = db.query(HomeworkItem).filter(HomeworkItem.batch_id == batch.id).all()
    images = db.query(BatchImage).filter(BatchImage.batch_id == batch.id).all()
    subjects = {s.id: s for s in db.query(Subject).all()}

    return HomeworkBatchResponse(
        id=batch.id,
        child_id=batch.child_id,
        name=batch.name,
        status=batch.status,
        deadline_at=batch.deadline_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=[_item_to_response(item, subjects[item.subject_id]) for item in items],
        images=[_image_to_response(img) for img in images],
        vlm_parse_result=None
    )
