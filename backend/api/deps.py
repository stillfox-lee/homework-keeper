"""
API 依赖项
"""
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.models import Family, Child
from backend.config import settings


async def get_current_family(
    db: Session = Depends(get_db),
    x_access_token: Optional[str] = Header(None),
) -> Family:
    """
    获取当前家庭

    优先级：
    1. Header 中的 X-Access-Token
    2. 默认令牌（本地开发）
    """
    token = x_access_token or settings.DEFAULT_FAMILY_TOKEN

    family = db.query(Family).filter(Family.access_token == token).first()
    if not family:
        raise HTTPException(status_code=401, detail="无效的访问令牌")

    return family


async def get_current_child(
    db: Session = Depends(get_db),
    family: Family = Depends(get_current_family),
) -> Child:
    """获取当前家庭的孩子"""
    child = db.query(Child).filter(Child.family_id == family.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="未找到孩子信息")

    return child
