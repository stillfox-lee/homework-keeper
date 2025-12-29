"""
数据库连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

# 数据库目录
DB_DIR = Path("./data")
DB_DIR.mkdir(exist_ok=True)

# 数据库文件路径
DATABASE_URL = f"sqlite:///{DB_DIR}/database.db"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 特有配置
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表和默认数据"""
    from backend.models import Base, Family, Child, Subject

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 检查是否已有数据
    db = SessionLocal()
    try:
        # 检查是否已初始化
        if db.query(Family).count() > 0:
            print("数据库已初始化")
            return

        # 创建默认家庭
        default_family = Family(name="我的家庭", access_token="default123")
        db.add(default_family)
        db.flush()  # 获取 ID

        # 创建默认孩子
        default_child = Child(family_id=default_family.id, name="孩子")
        db.add(default_child)

        # 创建默认科目
        subjects = [
            Subject(name="数学", color="#3B82F6", sort_order=1),
            Subject(name="语文", color="#EF4444", sort_order=2),
            Subject(name="英语", color="#10B981", sort_order=3),
            Subject(name="科学", color="#F59E0B", sort_order=4),
            Subject(name="其他", color="#6B7280", sort_order=99),
        ]
        db.add_all(subjects)

        db.commit()
        print("数据库初始化成功")
        print(f"默认家庭访问令牌: {default_family.access_token}")

    except Exception as e:
        db.rollback()
        print(f"数据库初始化失败: {e}")
    finally:
        db.close()
