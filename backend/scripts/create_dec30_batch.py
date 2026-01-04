"""
创建 12.30 号已完成批次，用于测试多批次效果
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from backend.database import DATABASE_URL

def create_dec30_batch():
    """创建 12.30 号已完成批次"""
    engine = create_engine(DATABASE_URL)

    # 创建测试数据日期（指定固定时间，避免时区问题）
    dec30_date = datetime(2024, 12, 30, 18, 0, 0)  # 12月30日 18:00
    completed_time = datetime(2024, 12, 30, 21, 30, 0)  # 当天 21:30 完成

    with engine.connect() as conn:
        # 1. 创建批次（状态为 completed）
        result = conn.execute(text("""
            INSERT INTO homework_batches (child_id, name, status, deadline_at, completed_at, created_at, updated_at)
            VALUES (:child_id, :name, :status, :deadline_at, :completed_at, :created_at, :updated_at)
        """), {
            "child_id": 1,
            "name": "12月30日作业",
            "status": "completed",
            "deadline_at": dec30_date,
            "completed_at": completed_time,
            "created_at": dec30_date,
            "updated_at": completed_time
        })
        batch_id = result.lastrowid
        print(f"✓ 创建批次 ID: {batch_id}")

        # 2. 创建作业项（全部为 done 状态）
        items = [
            {
                "subject_id": 2,  # 语文
                "text": "完成《看图说话》练习册第15-16页",
                "key_concept": "看图写话",
                "started_at": dec30_date.replace(hour=19, minute=0),
                "finished_at": dec30_date.replace(hour=19, minute=45),
            },
            {
                "subject_id": 1,  # 数学
                "text": "口算练习册第20页，每天10分钟",
                "key_concept": "口算",
                "started_at": dec30_date.replace(hour=19, minute=45),
                "finished_at": dec30_date.replace(hour=20, minute=0),
            },
            {
                "subject_id": 3,  # 英语
                "text": "跟读 Unit 5 单词和课文，家长签字",
                "key_concept": "跟读",
                "started_at": dec30_date.replace(hour=20, minute=0),
                "finished_at": dec30_date.replace(hour=20, minute=20),
            },
            {
                "subject_id": 1,  # 数学
                "text": "完成应用题3道，要求写出解题思路",
                "key_concept": "应用题",
                "started_at": dec30_date.replace(hour=20, minute=20),
                "finished_at": dec30_date.replace(hour=20, minute=50),
            },
            {
                "subject_id": 2,  # 语文
                "text": "背诵古诗《登鹳雀楼》和《静夜思》",
                "key_concept": "古诗背诵",
                "started_at": dec30_date.replace(hour=20, minute=50),
                "finished_at": dec30_date.replace(hour=21, minute=10),
            },
            {
                "subject_id": 4,  # 科学
                "text": "观察并记录一种植物的生长情况",
                "key_concept": "观察记录",
                "started_at": dec30_date.replace(hour=21, minute=10),
                "finished_at": dec30_date.replace(hour=21, minute=30),
            },
        ]

        for i, item in enumerate(items, 1):
            conn.execute(text("""
                INSERT INTO homework_items (batch_id, subject_id, text, key_concept, status, started_at, finished_at, created_at, updated_at)
                VALUES (:batch_id, :subject_id, :text, :key_concept, :status, :started_at, :finished_at, :created_at, :updated_at)
            """), {
                "batch_id": batch_id,
                "subject_id": item["subject_id"],
                "text": item["text"],
                "key_concept": item["key_concept"],
                "status": "done",
                "started_at": item["started_at"],
                "finished_at": item["finished_at"],
                "created_at": dec30_date,
                "updated_at": item["finished_at"],
            })
            print(f"  ✓ 作业项 {i}: {item['text'][:20]}...")

        # 提交事务
        conn.commit()

    print(f"\n✅ 12月30日批次创建完成！批次 ID: {batch_id}")
    print(f"   共 {len(items)} 项作业，全部已完成")

if __name__ == "__main__":
    create_dec30_batch()
