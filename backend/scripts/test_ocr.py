#!/usr/bin/env python
"""
OCR 识别测试脚本
用法: uv run python -m backend.scripts.test_ocr <图片路径> [--debug]
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.ocr_service import get_ocr_service


def main():
    if len(sys.argv) < 2:
        print("用法: uv run python -m backend.scripts.test_ocr <图片路径> [--debug]")
        sys.exit(1)

    image_path = sys.argv[1]
    debug = "--debug" in sys.argv

    if not Path(image_path).exists():
        print(f"错误: 文件不存在: {image_path}")
        sys.exit(1)

    print(f"正在识别: {image_path}")
    print("-" * 50)

    ocr_service = get_ocr_service()
    result = ocr_service.recognize_image(image_path, debug=debug)

    if result.success:
        print(f"\n识别结果:")
        print("-" * 50)
        print(result.text)
        print("-" * 50)

        if debug and result.lines and result.scores:
            print(f"\n详细信息:")
            print("-" * 50)
            for i, (line, score) in enumerate(zip(result.lines, result.scores)):
                print(f"  [{i}] {line} (置信度: {score:.2f})")
            print("-" * 50)
            print(f"共 {len(result.lines)} 行文本")
    else:
        print(f"识别失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
