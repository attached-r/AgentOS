"""
AgentOS Runtime —— FastAPI 入口。

V1 架构分层（从底到顶）：
  core/        — 基础组件：LLM 客户端、Message 模型、Agent 基类
  agents/      — Agent 实现：SimpleAgent、AgentRegistry
  api/         — 路由层：invoke、registry、health
  middlewares/ — 中间件：请求日志
  errors/      — 异常处理：统一错误响应

启动方式：
    cd runtime
    uv run uvicorn main:app --host 0.0.0.0 --port 8001 --reload

    或通过 main.py 直接启动：
    python main.py
"""
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError

# 加载 .env 文件（必须放在其他 import 之前）
load_dotenv()

from api.health import router as health_router
from api.registry_routes import router as registry_router
from api.invoke_routes import router as invoke_router
from config import get_config
from middlewares.logging import RequestLogMiddleware
from errors.handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

# ---------------------------------------------------------------------------
# 创建 FastAPI 应用
# ---------------------------------------------------------------------------

config = get_config()

app = FastAPI(
    title=config.runtime_title,
    version="1.0.0",
    description="AgentOS 智能体运行时 — Python 执行环境",
)

# ---------------------------------------------------------------------------
# 注册中间件（顺序重要：先注册的在外层）
# ---------------------------------------------------------------------------

app.add_middleware(RequestLogMiddleware)

# ---------------------------------------------------------------------------
# 注册异常处理器
# ---------------------------------------------------------------------------

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ---------------------------------------------------------------------------
# 注册路由
# ---------------------------------------------------------------------------

# 健康检查（不挂 prefix，后端直接 GET /health）
app.include_router(health_router, tags=["health"])

# Agent 注册管理：GET /runtime/agents, POST /runtime/agents/sync
app.include_router(
    registry_router,
    prefix="/runtime/agents",
    tags=["registry"],
)

# Agent 调用：POST /runtime/agents/{id}/invoke
app.include_router(
    invoke_router,
    prefix="/runtime/agents",
    tags=["invoke"],
)

# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.runtime_host,
        port=config.runtime_port,
        reload=config.runtime_debug,
        log_level=config.log_level.lower(),
    )
