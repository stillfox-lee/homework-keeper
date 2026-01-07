"""
配置文件
"""

from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    model_config = ConfigDict(extra="ignore", env_file=".env")

    # 应用配置
    APP_NAME: str = "墨宝"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/database.db"

    # 文件存储
    UPLOAD_DIR: Path = Path("./data/uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS（逗号分隔的字符串）
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    # 访问配置（用于生成完整图片 URL）
    DOMAIN: str = "localhost:8000"
    SUB_PATH: str = "/"

    # VLM 配置（智谱 GLM-4V-Flash）
    ZHIPU_API_KEY: str = ""
    VLM_MODEL: str = "glm-4.6v-flash"  # 免费多模态模型
    VLM_TIMEOUT: int = 60
    VLM_MAX_RETRIES: int = 3

    def _get_base_url(self) -> str:
        """获取完整的基础 URL（用于拼接图片 URL）

        - 自动根据 DOMAIN 判断使用 http:// 或 https://
        - 自动处理 SUB_PATH 首尾斜杠
        """
        # 处理协议：如果 DOMAIN 已包含协议则使用，否则默认 http://
        domain = self.DOMAIN.strip()
        if not domain.startswith("http://") and not domain.startswith("https://"):
            domain = f"http://{domain}"
        # 去除 DOMAIN 末尾的斜杠
        domain = domain.rstrip("/")

        # 处理 SUB_PATH：去除首尾斜杠
        sub_path = self.SUB_PATH.strip().strip("/")

        # 拼接完整 URL
        if sub_path:
            return f"{domain}/{sub_path}"
        return domain

    # 兼容属性访问方式
    BASE_URL = property(_get_base_url)


settings = Settings()

# 确保上传目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
