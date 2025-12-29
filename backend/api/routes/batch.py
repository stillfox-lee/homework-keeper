"""
作业批次管理 API
"""
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
)

router = APIRouter(prefix="/api/batches", tags=["batches"])


def _subject_response_dict(subject: Subject) -> dict:
    """科目转字典"""
    return {
        "id": subject.id,
        "name": subject.name,
        "color": subject.color,
        "sort_order": subject.sort_order
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
        created_at=item.created_at
    )


def _batch_to_response(batch: HomeworkBatch) -> HomeworkBatchResponse:
    """批次转响应"""
    return HomeworkBatchResponse(
        id=batch.id,
        child_id=batch.child_id,
        name=batch.name,
        status=batch.status,
        deadline_at=batch.deadline_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=[],
        images=[]
    )


@router.get("", response_model=List[HomeworkBatchResponse])
async def get_batches(
    status: Optional[str] = None,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """获取批次列表"""
    query = db.query(HomeworkBatch).filter(HomeworkBatch.child_id == child.id)

    if status:
        query = query.filter(HomeworkBatch.status == status)

    batches = query.order_by(HomeworkBatch.created_at.desc()).all()

    return [_batch_to_response(b) for b in batches]


@router.get("/current", response_model=Optional[HomeworkBatchResponse])
async def get_current_batch(
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
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
    response.items = [_item_to_response(item, subjects[item.subject_id]) for item in items]

    return response


@router.get("/{batch_id}", response_model=HomeworkBatchResponse)
async def get_batch(
    batch_id: int,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """获取批次详情"""
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 加载作业项和图片
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
        images=[
            BatchImageResponse(
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
            for img in images
        ]
    )


@router.get("/{batch_id}/items", response_model=List[HomeworkItemResponse])
async def get_batch_items(
    batch_id: int,
    status: Optional[str] = None,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """获取批次的作业项列表"""
    # 验证批次所有权
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

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
    db: Session = Depends(get_db)
):
    """向批次添加作业项"""
    # 验证批次所有权
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

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
        status='todo'
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
    db: Session = Depends(get_db)
):
    """更新批次状态"""
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    if data.status not in ['draft', 'active', 'completed']:
        raise HTTPException(status_code=400, detail="无效的状态")

    if data.status == 'active':
        homework_service = get_homework_service()
        homework_service.activate_batch(db, batch_id)
    elif data.status == 'completed':
        batch.status = 'completed'
        batch.completed_at = datetime.utcnow()
    else:
        batch.status = data.status

    db.commit()
    db.refresh(batch)

    return {"success": True, "data": _batch_to_response(batch)}


@router.delete("/{batch_id}")
async def delete_batch(
    batch_id: int,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """删除批次"""
    batch = db.query(HomeworkBatch).filter(
        HomeworkBatch.id == batch_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 删除关联的图片文件
    images = db.query(BatchImage).filter(BatchImage.batch_id == batch_id).all()
    for img in images:
        import os
        file_path = f"data/uploads/{img.file_path}"
        if os.path.exists(file_path):
            os.remove(file_path)

    # 删除数据库记录（级联删除会处理 items）
    db.delete(batch)
    db.commit()

    return {"success": True, "message": "批次已删除"}
