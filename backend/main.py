"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from backend.config import settings
from backend.api.routes import batch, items, subject, analytics, family, v1_upload
from backend.middleware import RequestIdMiddleware
from backend.core.request import configure_logger_with_request_id

# 配置日志（包含 request-id）
configure_logger_with_request_id()

from loguru import logger

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# 注册 Request-ID 中间件（必须在 CORS 之前）
app.add_middleware(RequestIdMiddleware)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(batch.router)
app.include_router(items.router)
app.include_router(subject.router)
app.include_router(analytics.router)
app.include_router(family.router)
# V1 路由（使用 VLM）
app.include_router(v1_upload.router)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/")
async def index():
    """主页 - 返回前端页面"""
    return FileResponse("frontend/index.html")


# HTML 页面路由（新增页面时在此添加）
@app.get("/today.html")
async def today_page():
    return FileResponse("frontend/today.html")


@app.get("/registry.html")
async def registry_page():
    return FileResponse("frontend/registry.html")


@app.get("/{file_name:path}.html")
async def html_files(file_name: str):
    """通用 HTML 文件路由 - 新增页面无需再添加路由"""
    return FileResponse(f"frontend/{file_name}.html")


@app.get("/family/{token}")
async def family_index(token: str):
    """家庭访问入口 - 返回前端页面（token 由前端使用）"""
    return FileResponse("frontend/index.html")


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    from backend.database import init_db
    init_db()
    logger.info("Application started successfully")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
