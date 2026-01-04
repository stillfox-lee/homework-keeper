"""
作业批次管理服务
"""
from datetime import datetime, timedelta, date, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
import pytz

from backend.models import HomeworkBatch, BatchImage, HomeworkItem, Child, Subject
from backend.services.holiday_service import get_holiday_service


class HomeworkService:
    """作业批次管理服务"""

    def generate_batch_name(self) -> str:
        """
        生成批次名称

        规则：
        - 学期周中用日期命名（如"12月29日作业"）
        """
        local_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(timezone.utc).astimezone(local_tz)
        return f"{now.month}月{now.day}日作业"

    def calculate_deadline(self, base_date: Optional[datetime] = None) -> datetime:
        """
        智能计算截止时间（考虑法定节假日）

        规则：
        - 工作日创建 → 次个工作日 23:59（如果是假期则顺延）
        - 周五/假期前创建 → 找到假期结束后的第一天
        - 周末/假期中 → 找到假期/周末结束后的第一天

        Args:
            base_date: 基准日期（UTC 时间），默认为当前 UTC 时间

        Returns:
            截止时间（UTC 时间）
        """
        local_tz = pytz.timezone('Asia/Shanghai')

        if base_date is None:
            base_date = datetime.now(timezone.utc)

        # 确保 base_date 是带时区的 UTC 时间
        if base_date.tzinfo is None:
            base_date = base_date.replace(tzinfo=timezone.utc)

        # 转换为本地时区进行日期计算
        local_date = base_date.astimezone(local_tz)

        holiday_service = get_holiday_service()

        # 使用 UTC 日期计算（避免跨时区导致的日期跳变问题）
        # 例如：UTC 1月4日 16:10 = 东八区 1月5日 00:10
        # 用户在东八区 1月4日晚上创建，deadline 应该是 1月5日（基于 UTC 日期的次日）
        base_utc_date = base_date.date()
        deadline_date = base_utc_date + timedelta(days=1)

        # 如果次日不是工作日，继续往后找
        while not holiday_service.is_workday(deadline_date):
            deadline_date = deadline_date + timedelta(days=1)
            # 最多往后找30天，防止无限循环
            if (deadline_date - base_utc_date).days > 30:
                break

        # 组合为本地 datetime（23:59:59），然后转回 UTC 存储
        local_deadline = local_tz.localize(
            datetime.combine(deadline_date, datetime.min.time())
        ).replace(hour=23, minute=59, second=59)

        return local_deadline.astimezone(timezone.utc).replace(tzinfo=None)

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
            status='draft',
            deadline_at=self.calculate_deadline()  # 预计算截止时间
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
