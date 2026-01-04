"""
统计分析 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from backend.database import get_db
from backend.models import HomeworkBatch, HomeworkItem, Subject
from backend.api.deps import get_current_child

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/daily")
async def get_daily_stats(
    start_date: str = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期 YYYY-MM-DD"),
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """
    获取每日作业统计

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        每日统计数据
    """
    # 默认最近 7 天
    if not end_date:
        end_date = datetime.utcnow().date()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    if not start_date:
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    # 查询日期范围内的批次
    batches = db.query(HomeworkBatch).filter(
        HomeworkBatch.child_id == child.id,
        func.date(HomeworkBatch.created_at) >= start_date,
        func.date(HomeworkBatch.created_at) <= end_date
    ).all()

    # 获取所有相关作业项
    batch_ids = [b.id for b in batches]
    items = db.query(HomeworkItem).filter(HomeworkItem.batch_id.in_(batch_ids)).all()

    # 统计
    total_count = len(items)
    completed_count = len([i for i in items if i.status == 'done'])

    # 计算平均用时
    durations = []
    for item in items:
        if item.started_at and item.finished_at:
            duration = (item.finished_at - item.started_at).total_seconds() / 60
            durations.append(duration)

    avg_duration = sum(durations) / len(durations) if durations else 0

    # 每日统计
    daily_stats = []
    current_date = start_date
    while current_date <= end_date:
        day_batches = [
            b for b in batches
            if b.created_at.date() == current_date
        ]
        day_batch_ids = [b.id for b in day_batches]
        day_items = [i for i in items if i.batch_id in day_batch_ids]
        day_completed = len([i for i in day_items if i.status == 'done'])

        daily_stats.append({
            "date": current_date.isoformat(),
            "total": len(day_items),
            "completed": day_completed
        })
        current_date += timedelta(days=1)

    return {
        "success": True,
        "data": {
            "total_count": total_count,
            "completed_count": completed_count,
            "completion_rate": completed_count / total_count if total_count > 0 else 0,
            "avg_duration_minutes": round(avg_duration, 1),
            "daily_stats": daily_stats
        }
    }


@router.get("/subject")
async def get_subject_stats(
    child=Depends(get_current_child),
    db: Session = Depends(get_db)
):
    """
    获取科目统计

    Returns:
        按科目分组的统计数据
    """
    # 获取孩子的所有批次
    batches = db.query(HomeworkBatch).filter(HomeworkBatch.child_id == child.id).all()
    batch_ids = [b.id for b in batches]

    # 获取所有作业项
    items = db.query(HomeworkItem).filter(HomeworkItem.batch_id.in_(batch_ids)).all()

    # 按科目分组统计
    subject_stats = {}
    for item in items:
        subject = db.query(Subject).filter(Subject.id == item.subject_id).first()
        if not subject:
            continue

        if subject.name not in subject_stats:
            subject_stats[subject.name] = {
                "subject": subject.name,
                "color": subject.color,
                "total_count": 0,
                "completed_count": 0,
                "durations": []
            }

        subject_stats[subject.name]["total_count"] += 1
        if item.status == 'done':
            subject_stats[subject.name]["completed_count"] += 1

        if item.started_at and item.finished_at:
            duration = (item.finished_at - item.started_at).total_seconds() / 60
            subject_stats[subject.name]["durations"].append(duration)

    # 计算平均值并格式化
    result = []
    for stats in subject_stats.values():
        durations = stats.pop("durations", [])
        stats["avg_duration_minutes"] = round(sum(durations) / len(durations), 1) if durations else 0
        result.append(stats)

    # 按完成数量排序
    result.sort(key=lambda x: x["completed_count"], reverse=True)

    return {
        "success": True,
        "data": result
    }
