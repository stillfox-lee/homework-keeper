"""
项目初始化脚本
用法: uv run init
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import init_db


def init_all():
    """执行所有初始化步骤"""
    print("=" * 50)
    print("作业管理系统 - 项目初始化")
    print("=" * 50)

    # 初始化数据库
    print("\n[1/1] 初始化数据库...")
    init_db()

    print("\n" + "=" * 50)
    print("初始化完成！")
    print("运行 'uv run uvicorn backend.main:app --reload' 启动服务")
    print("=" * 50)


if __name__ == "__main__":
    init_all()
