"""
作业项管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.models import HomeworkItem, HomeworkBatch, Subject
from backend.api.deps import get_current_child
from backend.schemas import HomeworkItemResponse, HomeworkItemUpdate, HomeworkItemStatusUpdate

router = APIRouter(prefix="/api/items", tags=["items"])


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
    response = HomeworkItemResponse.model_validate(item)
    response.subject = _subject_response_dict(subject)  # type: ignore
    return response


@router.put("/{item_id}", response_model=HomeworkItemResponse)
async def update_item(
    item_id: int,
    data: HomeworkItemUpdate,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """更新作业项"""
    # 通过 batch 验证所有权
    item = db.query(HomeworkItem).join(HomeworkBatch).filter(
        HomeworkItem.id == item_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="作业项不存在")

    # 更新字段
    if data.subject_id is not None:
        item.subject_id = data.subject_id
    if data.text is not None:
        item.text = data.text
    if data.key_concept is not None:
        item.key_concept = data.key_concept

    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    subject = db.query(Subject).filter(Subject.id == item.subject_id).first()
    return _item_to_response(item, subject)


@router.patch("/{item_id}/status", response_model=HomeworkItemResponse)
async def update_item_status(
    item_id: int,
    data: HomeworkItemStatusUpdate,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """更新作业项状态"""
    if data.status not in ["todo", "doing", "done"]:
        raise HTTPException(status_code=400, detail="无效的状态")

    # 通过 batch 验证所有权
    item = db.query(HomeworkItem).join(HomeworkBatch).filter(
        HomeworkItem.id == item_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="作业项不存在")

    item.status = data.status
    item.updated_at = datetime.utcnow()

    # 状态转换时记录时间
    if data.status == "doing" and not item.started_at:
        item.started_at = datetime.utcnow()
    elif data.status == "done" and not item.finished_at:
        item.finished_at = datetime.utcnow()
    elif data.status == "todo":
        item.started_at = None
        item.finished_at = None

    db.commit()
    db.refresh(item)

    # 检查并更新批次完成状态
    from backend.services.homework_service import get_homework_service
    homework_service = get_homework_service()
    batch = db.query(HomeworkBatch).filter(HomeworkBatch.id == item.batch_id).first()
    if batch:
        homework_service.update_batch_completion(db, batch)

    subject = db.query(Subject).filter(Subject.id == item.subject_id).first()
    return _item_to_response(item, subject)


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """删除作业项"""
    # 通过 batch 验证所有权
    item = db.query(HomeworkItem).join(HomeworkBatch).filter(
        HomeworkItem.id == item_id,
        HomeworkBatch.child_id == child.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="作业项不存在")

    db.delete(item)
    db.commit()

    return {"success": True, "message": "作业项已删除"}
