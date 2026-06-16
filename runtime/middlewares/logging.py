"""
日志中间件 —— 为每个请求注入唯一 Request ID，记录请求耗时。

功能：
  1. 为每个请求生成 trace_id（格式：req-{timestamp}-{random}）
  2. 在 response header 中返回 trace_id，便于链路追踪
  3. 记录请求方法、路径、状态码、耗时
"""
import time
import logging
import random

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("agentos.runtime")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件。

    为每个请求注入 X-Trace-Id 头，并记录请求耗时日志。
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # 生成 trace_id：时间戳 + 随机后缀，保证唯一性
        trace_id = f"req-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"

        # 将 trace_id 注入 request.state，供后续 handler 使用
        request.state.trace_id = trace_id

        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception as exc:
            # 未捕获的异常 —— 记录日志后继续抛出，由全局异常处理器处理
            logger.error(
                "[%s] %s %s 未捕获异常: %s",
                trace_id, request.method, request.url.path, exc,
            )
            raise

        # 计算耗时
        elapsed_ms = (time.time() - start_time) * 1000

        # 将 trace_id 写入响应头，便于客户端链路追踪
        response.headers["X-Trace-Id"] = trace_id

        # 记录请求日志
        logger.info(
            "[%s] %s %s → %d (%.1fms)",
            trace_id, request.method, request.url.path,
            response.status_code, elapsed_ms,
        )

        return response
