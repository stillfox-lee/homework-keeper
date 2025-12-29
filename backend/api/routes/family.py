"""
家庭相关 API
"""
import secrets
import string
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Family, Child
from backend.schemas import FamilyCreate, FamilyResponse
from backend.api.deps import get_current_family

router = APIRouter(prefix="/api/family", tags=["family"])


def generate_access_token(length: int = 16) -> str:
    """生成随机访问令牌"""
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("", response_model=FamilyResponse)
async def create_family(
    data: FamilyCreate,
    db: Session = Depends(get_db)
):
    """创建新家庭"""
    # 检查名称是否重复
    existing = db.query(Family).filter(Family.name == data.name).first()
    if existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="家庭名称已存在")

    # 生成唯一令牌
    token = generate_access_token()
    while db.query(Family).filter(Family.access_token == token).first():
        token = generate_access_token()

    # 创建家庭
    family = Family(name=data.name, access_token=token)
    db.add(family)
    db.flush()

    # 创建孩子
    child = Child(family_id=family.id, name=data.child_name)
    db.add(child)

    db.commit()
    db.refresh(family)

    return FamilyResponse(
        id=family.id,
        name=family.name,
        access_token=family.access_token,
        child=ChildResponse(
            id=child.id,
            family_id=child.family_id,
            name=child.name
        )
    )


@router.get("/current", response_model=FamilyResponse)
async def get_current_family_info(
    family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """获取当前家庭信息"""
    child = db.query(Child).filter(Child.family_id == family.id).first()

    return FamilyResponse(
        id=family.id,
        name=family.name,
        access_token=family.access_token,
        child=ChildResponse(
            id=child.id,
            family_id=child.family_id,
            name=child.name
        )
    )
