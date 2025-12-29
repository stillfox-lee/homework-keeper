"""
项目初始化脚本
用法: uv run init
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import init_db
from backend.services.ocr_service import OCRService


def init_all():
    """执行所有初始化步骤"""
    print("=" * 50)
    print("作业管理系统 - 项目初始化")
    print("=" * 50)

    # 1. 初始化数据库
    print("\n[1/2] 初始化数据库...")
    init_db()

    # 2. 预下载 OCR 模型
    print("\n[2/2] 预下载 OCR 模型（首次运行需要下载约 100MB）...")
    init_ocr_models()

    print("\n" + "=" * 50)
    print("初始化完成！")
    print("运行 'uv run uvicorn backend.main:app --reload' 启动服务")
    print("=" * 50)


def init_ocr_models():
    """预下载 PaddleOCR 模型"""
    try:
        ocr_service = OCRService()
        # 强制初始化以下载模型
        ocr_service._ensure_initialized()
        if ocr_service.ocr is not None:
            print("OCR 模型已就绪")
        else:
            print("警告: OCR 初始化可能失败，首次使用时会重试")
    except Exception as e:
        print(f"OCR 模型下载失败: {e}")
        print("警告: 首次上传图片时会自动重试下载")


if __name__ == "__main__":
    init_all()
