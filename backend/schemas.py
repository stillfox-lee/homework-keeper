"""
Pydantic 数据验证模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== 响应模型 ====================

class SubjectResponse(BaseModel):
    """科目响应"""
    id: int
    name: str
    color: str
    sort_order: int

    class Config:
        from_attributes = True


class ChildResponse(BaseModel):
    """孩子响应"""
    id: int
    family_id: int
    name: str

    class Config:
        from_attributes = True


class BatchImageResponse(BaseModel):
    """批次图片响应"""
    id: int
    batch_id: int
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    sort_order: int
    image_type: str  # homework / reference
    raw_ocr_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HomeworkItemResponse(BaseModel):
    """作业项响应"""
    id: int
    batch_id: int
    source_image_id: Optional[int] = None
    subject: SubjectResponse
    text: str
    key_concept: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HomeworkBatchResponse(BaseModel):
    """作业批次响应"""
    id: int
    child_id: int
    name: str
    status: str
    deadline_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[HomeworkItemResponse] = []
    images: List[BatchImageResponse] = []

    class Config:
        from_attributes = True


# ==================== 请求模型 ====================

class HomeworkItemCreate(BaseModel):
    """创建作业项请求"""
    subject_id: int
    text: str
    key_concept: Optional[str] = None
    source_image_id: Optional[int] = None


class HomeworkItemUpdate(BaseModel):
    """更新作业项请求"""
    subject_id: Optional[int] = None
    text: Optional[str] = None
    key_concept: Optional[str] = None


class HomeworkItemStatusUpdate(BaseModel):
    """更新作业项状态请求"""
    status: str  # todo/doing/done


class BatchCreate(BaseModel):
    """创建批次请求"""
    name: Optional[str] = None  # 为空时系统自动生成


class BatchStatusUpdate(BaseModel):
    """更新批次状态请求"""
    status: str  # draft/active/completed


class DraftConfirmRequest(BaseModel):
    """确认 draft 批次请求"""
    items: List[HomeworkItemCreate]
    deadline_at: Optional[datetime] = None


# ==================== 上传相关 ====================

class DraftBatchInfo(BaseModel):
    """Draft 批次简要信息"""
    id: int
    name: str
    status: str


class UploadDraftResponse(BaseModel):
    """上传 draft 批次响应"""
    success: bool
    data: dict
    batch: DraftBatchInfo  # 批次信息
    batch_id: int
    images: List[BatchImageResponse]
    ocr_text: Optional[str] = None  # 合并后的 OCR 文本


class ParsedHomeworkItem(BaseModel):
    """LLM 解析出的作业项"""
    subject_id: int  # 科目ID
    subject_name: str  # 科目名称（用于显示）
    text: str  # 作业描述
    key_concept: Optional[str] = None


class LLMParseResponse(BaseModel):
    """LLM 解析响应"""
    success: bool
    items: List[ParsedHomeworkItem]


# ==================== 通用响应 ====================

class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


class FamilyCreate(BaseModel):
    """创建家庭请求"""
    name: str = Field(min_length=1, max_length=50)
    child_name: str = Field(min_length=1, max_length=50)


class FamilyResponse(BaseModel):
    """家庭响应"""
    id: int
    name: str
    access_token: str
    child: ChildResponse

    class Config:
        from_attributes = True
