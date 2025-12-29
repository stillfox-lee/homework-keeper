"""
作业批次管理服务
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models import HomeworkBatch, BatchImage, HomeworkItem, Child, Subject


class HomeworkService:
    """作业批次管理服务"""

    def generate_batch_name(self) -> str:
        """
        生成批次名称

        规则：
        - 学期周中用日期命名（如"12月29日作业"）
        """
        now = datetime.now()
        return f"{now.month}月{now.day}日作业"

    def calculate_deadline(self, base_date: Optional[datetime] = None) -> datetime:
        """
        智能计算截止时间

        规则：
        - 工作日创建 → 次日 23:59
        - 周五创建 → 周日 23:59
        - 周六创建 → 周日 23:59
        - 周日创建 → 当晚 23:59（或周一）

        Args:
            base_date: 基准日期，默认为当前时间

        Returns:
            截止时间
        """
        if base_date is None:
            base_date = datetime.now()

        weekday = base_date.weekday()  # 0=周一, 6=周日

        if weekday == 4:  # 周五
            # 截止到周日
            deadline = base_date + timedelta(days=2)
        elif weekday == 5:  # 周六
            # 截止到周日
            deadline = base_date + timedelta(days=1)
        elif weekday == 6:  # 周日
            # 截止到周一（或当晚，这里设置为周一）
            deadline = base_date + timedelta(days=1)
        else:  # 周一到周四
            # 截止到次日
            deadline = base_date + timedelta(days=1)

        # 设置为 23:59
        return deadline.replace(hour=23, minute=59, second=59)

    def create_draft_batch(
        self,
        db: Session,
        child_id: int,
        name: Optional[str] = None
    ) -> HomeworkBatch:
        """
        创建 draft 状态的批次

        Args:
            db: 数据库会话
            child_id: 孩子ID
            name: 批次名称，为空时自动生成

        Returns:
            创建的批次
        """
        if name is None:
            name = self.generate_batch_name()

        batch = HomeworkBatch(
            child_id=child_id,
            name=name,
            status='draft'
        )
        db.add(batch)
        db.flush()

        return batch

    def get_active_batch(self, db: Session, child_id: int) -> Optional[HomeworkBatch]:
        """
        获取当前 active 状态的批次

        Args:
            db: 数据库会话
            child_id: 孩子ID

        Returns:
            active 批次，不存在则返回 None
        """
        return db.query(HomeworkBatch).filter(
            HomeworkBatch.child_id == child_id,
            HomeworkBatch.status == 'active'
        ).first()

    def get_latest_batch(self, db: Session, child_id: int) -> Optional[HomeworkBatch]:
        """
        获取最新的批次（draft 或 active）

        Args:
            db: 数据库会话
            child_id: 孩子ID

        Returns:
            最新批次，不存在则返回 None
        """
        return db.query(HomeworkBatch).filter(
            HomeworkBatch.child_id == child_id,
            HomeworkBatch.status.in_(['draft', 'active'])
        ).order_by(HomeworkBatch.created_at.desc()).first()

    def complete_active_batch(self, db: Session, child_id: int) -> None:
        """
        完成当前的 active 批次

        Args:
            db: 数据库会话
            child_id: 孩子ID
        """
        active_batch = self.get_active_batch(db, child_id)
        if active_batch:
            active_batch.status = 'completed'
            active_batch.completed_at = datetime.utcnow()

    def activate_batch(self, db: Session, batch_id: int) -> HomeworkBatch:
        """
        激活批次（draft → active），自动完成之前的 active 批次

        Args:
            db: 数据库会话
            batch_id: 批次ID

        Returns:
            激活后的批次
        """
        batch = db.query(HomeworkBatch).filter(
            HomeworkBatch.id == batch_id
        ).first()

        if not batch:
            raise ValueError(f"批次 {batch_id} 不存在")

        # 获取该批次的孩子
        child_id = batch.child_id

        # 完成之前的 active 批次
        self.complete_active_batch(db, child_id)

        # 设置 deadline（如果还没有）
        if batch.deadline_at is None:
            batch.deadline_at = self.calculate_deadline()

        # 激活当前批次
        batch.status = 'active'
        batch.updated_at = datetime.utcnow()

        db.flush()
        return batch

    def check_batch_completion(self, db: Session, batch_id: int) -> bool:
        """
        检查批次是否完成（所有作业项都是 done 状态）

        Args:
            db: 数据库会话
            batch_id: 批次ID

        Returns:
            是否完成
        """
        items = db.query(HomeworkItem).filter(
            HomeworkItem.batch_id == batch_id
        ).all()

        if not items:
            return False

        return all(item.status == 'done' for item in items)

    def update_batch_completion(self, db: Session, batch: HomeworkBatch) -> None:
        """
        更新批次的完成状态

        Args:
            db: 数据库会话
            batch: 批次对象
        """
        if self.check_batch_completion(db, batch.id):
            if batch.status != 'completed':
                batch.status = 'completed'
                batch.completed_at = datetime.utcnow()


# 全局单例
_homework_service = None


def get_homework_service() -> HomeworkService:
    """获取作业服务单例"""
    global _homework_service
    if _homework_service is None:
        _homework_service = HomeworkService()
    return _homework_service
