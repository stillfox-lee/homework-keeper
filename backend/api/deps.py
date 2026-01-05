"""
API 依赖项
"""
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.models import Family, Child
from backend.core.request import get_request_id as get_current_request_id


async def get_current_family(
    db: Session = Depends(get_db),
    x_access_token: Optional[str] = Header(None),
) -> Family:
    """
    获取当前家庭

    从 Header 中的 X-Access-Token 获取认证信息
    """
    if not x_access_token:
        raise HTTPException(status_code=401, detail="缺少访问令牌")

    family = db.query(Family).filter(Family.access_token == x_access_token).first()
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


async def get_request_id() -> str:
    """
    获取当前请求的 request-id

    可以在路由处理函数中通过依赖注入使用：

    ```python
    @router.get("/items")
    async def get_items(request_id: str = Depends(get_request_id)):
        # 使用 request_id 进行日志记录或其他操作
        logger.info(f"Processing request {request_id}")
    ```

    Returns:
        当前请求的 request-id
    """
    return get_current_request_id()
