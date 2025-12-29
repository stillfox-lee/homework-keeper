"""
科目相关 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import Subject
from backend.schemas import SubjectResponse

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectResponse])
async def get_subjects(
    db: Session = Depends(get_db)
):
    """获取所有科目列表（系统预定义，所有家庭共享）"""
    subjects = db.query(Subject).order_by(Subject.sort_order).all()
    return subjects
