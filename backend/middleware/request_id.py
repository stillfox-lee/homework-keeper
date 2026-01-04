"""
Request-ID 追踪中间件

功能：
1. 从请求头读取已有的 request-id（支持跨服务调用）
2. 如果没有则生成新的 UUID
3. 将 request-id 存储到 contextvars 中
4. 在响应头中返回 X-Request-ID
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable

from backend.core.request import get_request_id, set_request_id, generate_request_id
from loguru import logger


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Request-ID 追踪中间件

    支持的请求头:
    - X-Request-ID

    生成的 request-id 会通过响应头 X-Request-ID 返回
    """

    # 响应头名称
    RESPONSE_HEADER = "x-request-id"

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> ASGIApp:
        """
        处理请求，注入 request-id

        Args:
            request: FastAPI/Starlette 请求对象
            call_next: 下一个中间件/路由处理器

        Returns:
            响应对象，带有 X-Request-ID 头
        """
        # 1. 尝试从请求头获取现有的 request-id
        request_id = request.headers.get(self.RESPONSE_HEADER, "")

        # 2. 如果没有则生成新的
        if not request_id:
            request_id = generate_request_id()

        # 3. 存储到 contextvars（供日志和业务代码使用）
        set_request_id(request_id)

        # 4. 记录请求开始日志
        logger.info(
            f"Request started: {request.method} {request.url.path}",
        )

        # 5. 调用下一个处理器
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed with exception: {e}")
            raise

        # 6. 将 request-id 添加到响应头
        response.headers[self.RESPONSE_HEADER] = request_id

        # 7. 记录请求完成日志
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
        )

        return response
