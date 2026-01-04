"""
Request 上下文管理
使用 contextvars 在异步环境中存储 request-id
"""
import contextvars
import uuid
from pathlib import Path
from loguru import logger

# 用于在异步上下文中存储 request-id
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def get_request_id() -> str:
    """
    获取当前请求的 request-id

    Returns:
        当前请求的 request-id，如果未设置则返回空字符串
    """
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """
    设置当前请求的 request-id

    Args:
        request_id: 要设置的 request-id
    """
    request_id_var.set(request_id)


def generate_request_id() -> str:
    """
    生成新的 request-id

    Returns:
        格式为 {uuid4} 的字符串，如 "a1b2c3d4-e5f6-4a5b-8c7d-9e8f7a6b5c4d"
    """
    return str(uuid.uuid4())


def configure_logger_with_request_id():
    """
    配置 loguru 日志格式，使其自动包含 request-id

    使用 logger.patch() 方法在每条日志记录时动态获取当前 request-id
    日志输出：
    - 控制台：彩色格式，DEBUG 级别
    - 文件：logs/app_{date}.log，INFO 级别，按天轮转，保留30天
    """

    def formatter(record):
        """自定义日志格式化函数"""
        # 获取当前请求的 request-id（从 contextvar）
        request_id = get_request_id()

        # 格式: [时间] [级别] [request-id] [模块:函数:行号] 消息
        if request_id:
            record["extra"]["request_id"] = request_id
        else:
            # 没有 request-id 时显示为 "N/A"
            record["extra"]["request_id"] = "N/A"

        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>[{extra[request_id]}]</cyan> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "{message}\n"
        )

    # 移除默认 handler
    logger.remove()

    # 添加控制台输出
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format=formatter,
        level="DEBUG",
        colorize=True,
    )

    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # 添加文件输出（带日志轮转）
    logger.add(
        sink=log_dir / "app_{time:YYYY-MM-DD}.log",
        format=formatter,
        level="INFO",
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        colorize=False,  # 文件输出不使用颜色
    )
