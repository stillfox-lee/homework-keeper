"""
Pydantic 数据验证模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== 基础配置 ====================

class BaseResponse(BaseModel):
    """基础响应模型，配置 datetime 序列化"""

    class Config:
        from_attributes = True
        # 确保 datetime 序列化为 ISO 格式时包含 UTC 时区标识符 'Z'
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None
        }


# ==================== 响应模型 ====================

class SubjectResponse(BaseResponse):
    """科目响应"""
    id: int
    name: str
    color: str
    sort_order: int


class ChildResponse(BaseResponse):
    """孩子响应"""
    id: int
    family_id: int
    name: str


class BatchImageResponse(BaseResponse):
    """批次图片响应"""
    id: int
    batch_id: int
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    sort_order: int
    image_type: str  # homework / reference
    raw_ocr_text: Optional[str] = None
    ocr_status: str  # pending/success/failed
    ocr_error: Optional[str] = None
    created_at: datetime


class HomeworkItemResponse(BaseResponse):
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


class HomeworkBatchResponse(BaseResponse):
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
    vlm_parse_result: Optional[dict] = None  # draft 状态时返回 VLM 解析结果


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


class HomeworkItemStatusResponse(BaseResponse):
    """作业项状态更新响应"""
    item: HomeworkItemResponse
    batch_ready_to_complete: bool = False  # 批次是否已准备好完成（全部 done 但还未 completed）


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

class DraftBatchInfo(BaseResponse):
    """Draft 批次简要信息"""
    id: int
    name: str
    status: str
    deadline_at: Optional[datetime] = None  # 预计算的截止时间


class UploadDraftResponse(BaseResponse):
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
    source_image_id: Optional[int] = None  # 来源图片 ID（VLM 解析时根据 homeworkFileName 映射）


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


# ==================== VLM 相关 ====================

class VLMParsedHomeworkItem(BaseModel):
    """VLM 解析出的作业项（原始格式）"""
    subject: str  # 科目名称
    text: str  # 作业描述
    homeworkFileName: str  # 作业图片文件名


class VLMImageClassification(BaseModel):
    """图片分类结果"""
    homework_images: List[int]  # homework 图片的 sort_order 列表
    reference_images: List[int]  # reference 图片的 sort_order 列表


class VLMParseResult(BaseModel):
    """VLM 完整解析结果"""
    success: bool
    classification: VLMImageClassification
    items: List[ParsedHomeworkItem]  # 映射后的作业项
    raw_items: List[VLMParsedHomeworkItem]  # 原始 VLM 返回
    unmatched_subjects: List[str] = []  # 未匹配的科目名（需要用户处理）
    error: Optional[str] = None


class VLMUploadDraftResponse(BaseResponse):
    """VLM 上传 draft 批次响应"""
    success: bool
    batch: DraftBatchInfo
    batch_id: int
    images: List[BatchImageResponse]
    parsed: Optional[VLMParseResult] = None


class VLMDraftConfirmRequest(BaseModel):
    """确认 VLM draft 批次请求"""
    items: List[HomeworkItemCreate]
    image_classification: Optional[VLMImageClassification] = None  # 用户可修改
    deadline_at: Optional[datetime] = None


# ==================== 批次更新相关 ====================

class HomeworkItemUpdateOrCreate(BaseModel):
    """更新或创建作业项（用于编辑模式）"""
    id: Optional[int] = None  # 有ID则更新，无ID则创建
    subject_id: int
    text: str
    key_concept: Optional[str] = None
    source_image_id: Optional[int] = None


class BatchUpdate(BaseModel):
    """更新批次请求"""
    name: Optional[str] = None
    deadline_at: Optional[datetime] = None
    items: Optional[List[HomeworkItemUpdateOrCreate]] = None  # 完全替换作业项列表
