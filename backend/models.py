"""
SQLAlchemy 数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from datetime import datetime


class Base:
    """所有模型的基类"""
    pass


# 导入 SQLAlchemy 的 Base
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(cls=Base)


# ==================== 基础表 ====================

class Family(Base):
    """家庭表"""
    __tablename__ = "families"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    access_token = Column(String(32), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())


class Child(Base):
    """孩子表"""
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(Integer, nullable=False)
    name = Column(String(50), nullable=False)


class Subject(Base):
    """科目表（系统预定义，所有家庭共享）"""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), default="#3B82F6")
    sort_order = Column(Integer, default=0)


# ==================== 批次相关表 ====================

class HomeworkBatch(Base):
    """作业批次表"""
    __tablename__ = "homework_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, nullable=False)

    # 批次信息
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft/active/completed

    # 时间管理
    deadline_at = Column(DateTime)
    completed_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class BatchImage(Base):
    """批次图片表"""
    __tablename__ = "batch_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, nullable=False)

    # 图片信息
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    sort_order = Column(Integer, default=0)

    # 图片类型: homework(作业清单) / reference(参考资料)
    image_type = Column(String(20), default="homework")

    # OCR 结果
    raw_ocr_text = Column(Text)

    created_at = Column(DateTime, server_default=func.current_timestamp())


class HomeworkItem(Base):
    """作业项表"""
    __tablename__ = "homework_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, nullable=False)
    source_image_id = Column(Integer)  # 来源图片，手动添加时为空
    subject_id = Column(Integer, nullable=False)

    # 作业内容
    text = Column(Text, nullable=False)
    key_concept = Column(String(100))

    # 状态管理
    status = Column(String(10), nullable=False, default="todo")  # todo/doing/done
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
