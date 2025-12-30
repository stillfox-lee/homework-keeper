"""
配置文件
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "作业管家"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/database.db"

    # 文件存储
    UPLOAD_DIR: Path = Path("./data/uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: list = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # 默认家庭令牌（本地开发使用）
    DEFAULT_FAMILY_TOKEN: str = "default123"

    # VLM 配置（智谱 GLM-4V-Flash）
    ZHIPU_API_KEY: str = ""
    VLM_MODEL: str = "glm-4.6v-flash"  # 免费多模态模型
    VLM_TIMEOUT: int = 60
    VLM_MAX_RETRIES: int = 3

    class Config:
        env_file = ".env"


settings = Settings()

# 确保上传目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
