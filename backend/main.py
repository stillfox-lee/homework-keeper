"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from backend.config import settings
from backend.api.routes import batch, items, subject, upload, analytics, family

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(batch.router)
app.include_router(items.router)
app.include_router(subject.router)
app.include_router(upload.router)
app.include_router(analytics.router)
app.include_router(family.router)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/")
async def index():
    """主页 - 返回前端页面"""
    return FileResponse("frontend/index.html")


@app.get("/family/{token}")
async def family_index(token: str):
    """家庭访问入口 - 返回前端页面（token 由前端使用）"""
    return FileResponse("frontend/index.html")


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    from backend.database import init_db
    init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
