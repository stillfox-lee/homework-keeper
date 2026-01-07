"""
用户管理脚本

用法:
  uv run add-user --family "家庭名" --child "孩子名"
"""
import sys
import argparse
import secrets
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_base_url() -> str:
    """获取应用基础 URL"""
    domain = os.getenv("DOMAIN", "localhost:8000")
    sub_path = os.getenv("SUB_PATH", "").rstrip("/")
    return f"http://{domain}{sub_path}"

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import SessionLocal
from backend.models import Family, Child


def generate_token() -> str:
    """生成 32 位随机 access token"""
    return secrets.token_hex(16)


def create_or_get_family(db, name: str) -> Family:
    """创建或获取家庭"""
    family = db.query(Family).filter(Family.name == name).first()
    if family:
        print(f"家庭 '{name}' 已存在，使用现有家庭")
        return family

    token = generate_token()
    family = Family(name=name, access_token=token)
    db.add(family)
    db.flush()
    print(f"✓ 创建家庭: {name}")
    return family


def create_child(db, family_id: int, name: str) -> Child:
    """创建孩子"""
    # 检查是否已存在同名孩子
    existing = db.query(Child).filter(
        Child.family_id == family_id,
        Child.name == name
    ).first()
    if existing:
        print(f"  孩子 '{name}' 已存在，跳过")
        return existing

    child = Child(family_id=family_id, name=name)
    db.add(child)
    db.flush()
    print(f"  ✓ 创建孩子: {name}")
    return child


def main():
    parser = argparse.ArgumentParser(description="创建家庭和孩子")
    parser.add_argument("--family", required=True, help="家庭名称")
    parser.add_argument("--child", required=True, help="孩子名称")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        family = create_or_get_family(db, args.family)
        create_child(db, family.id, args.child)

        db.commit()

        print("\n" + "=" * 50)
        print("设置完成！")
        base_url = get_base_url()
        print(f"访问地址: {base_url}/?token={family.access_token}")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
