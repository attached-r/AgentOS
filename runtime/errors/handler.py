"""
全局异常处理器 —— 统一 FastAPI 的错误响应格式。

所有未捕获的异常最终落在此处，被转换为统一的 JSON 响应：
  {
    "detail": "错误描述",
    "error_code": "ERROR_CODE",
    "trace_id": "req-..."
  }

错误码约定（参考阶段v1文档 7.3 节）：
  - AGENT_NOT_FOUND    — Agent 不存在（404）
  - LLM_CALL_FAILED    — LLM API 调用失败（502）
  - RUNTIME_INTERNAL   — 运行时内部错误（500）
  - INVALID_REQUEST    — 请求参数校验失败（400）
"""
import logging

from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("agentos.runtime")

# 标准错误码映射
ERROR_CODES = {
    400: "INVALID_REQUEST",
    404: "AGENT_NOT_FOUND",
    502: "LLM_CALL_FAILED",
    500: "RUNTIME_INTERNAL",
}


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException 处理器 —— 将异常转为统一 JSON 格式。"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": ERROR_CODES.get(exc.status_code, "UNKNOWN"),
            "trace_id": trace_id,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求参数校验失败处理器。"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=422,
        content={
            "detail": str(exc.errors()),
            "error_code": "VALIDATION_ERROR",
            "trace_id": trace_id,
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """兜底异常处理器 —— 捕获所有未预期的异常。"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.exception("[%s] 未预期异常: %s", trace_id, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "运行时内部错误",
            "error_code": "RUNTIME_INTERNAL",
            "trace_id": trace_id,
        },
    )
