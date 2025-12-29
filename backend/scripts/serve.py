"""
启动开发服务器
用法: uv run serve [--reload]
"""
import uvicorn
import sys


def main():
    """启动 FastAPI 开发服务器"""
    reload = "--reload" in sys.argv
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload
    )


if __name__ == "__main__":
    main()
