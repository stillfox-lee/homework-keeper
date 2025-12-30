#!/usr/bin/env python
"""
VLM 解析测试脚本

测试纯 LLM 返回的 Pydantic 对象，不涉及数据库操作。

用法:
    uv run python -m backend.scripts.test_vlm <图片路径>...

示例:
    uv run python -m backend.scripts.test_vlm photo1.jpg photo2.jpg
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.homework_parser_service import get_homework_parser_service


# 默认科目列表
DEFAULT_SUBJECTS = [
    "语文",
    "数学",
    "英语",
    "物理",
    "化学",
    "生物",
    "地理",
    "历史",
    "政治",
]


def print_separator(char="=", length=60):
    """打印分隔线"""
    print(char * length)


async def main():
    # 解析参数
    image_paths = []

    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.exists():
            image_paths.append(str(path))
        else:
            print(f"警告: 文件不存在: {arg}")

    if not image_paths:
        print("用法: uv run python -m backend.scripts.test_vlm <图片路径>...")
        sys.exit(1)

    print_separator()
    print("VLM 解析测试")
    print_separator()
    print(f"图片数量: {len(image_paths)}")
    print(f"科目列表: {', '.join(DEFAULT_SUBJECTS)}")
    print_separator()

    # 获取服务并调用
    parser = get_homework_parser_service()

    try:
        vlm_output = await parser.call_llm_only(
            image_paths=image_paths,
            subject_names=DEFAULT_SUBJECTS,
        )

        # 输出结果
        print("\n✅ 解析成功!\n")
        print_separator()

        print(f"📷 作业图片: {vlm_output.homeworkFileName}")
        print(f"📚 参考资料图片: {vlm_output.referenceFileName}")

        print_separator()
        print(f"📝 作业项数量: {len(vlm_output.homework_items)}")
        print_separator()

        print_separator()
        print("\nJSON 输出:")
        print(vlm_output.model_dump_json(ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"\n❌ 解析失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
