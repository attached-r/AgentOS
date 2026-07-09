"""
运行时配置 —— 从环境变量加载所有可配置项。

集中管理所有配置项，而不是散落在各个模块中。
所有配置项都有默认值，通过 `.env` 文件或环境变量覆盖。
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RuntimeConfig:
    """
    运行时全局配置。

    加载优先级：环境变量（或 .env 文件）> 默认值

    用法：
        config = RuntimeConfig.from_env()
        print(config.runtime_host)
    """

    # ── FastAPI 服务 ──────────────────────────────────────────────
    runtime_host: str = "0.0.0.0"
    runtime_port: int = 8000
    runtime_debug: bool = False
    runtime_title: str = "AgentOS Runtime"
    log_level: str = "INFO"

    # ── LLM 默认值 ────────────────────────────────────────────────
    default_model_provider: str = "openai"
    default_model_name: str = "gpt-4o-mini"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    # ── 后端 API（Runtime → Backend 回调，用于持久化记忆 / RAG）──
    backend_base_url: str = "http://localhost:8099"

    # ── ReAct Agent ──────────────────────────────────────────
    react_max_steps: int = 10

    # ── Redis 工作记忆 ──────────────────────────────────────────
    # WorkingMemory 用 Redis 替代内存 List（V2.1 升级）
    # 从 .env 统一加载，不硬编码
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_wm_db: int = 1                     # 工作记忆独立 db，与后端 Redis 隔离
    redis_wm_ttl: int = 3600                 # 工作记忆 TTL（秒），默认 1 小时
    redis_wm_capacity: int = 100             # 单个 Agent 工作记忆容量上限

    # ── MCP 超时（秒）─────────────────────────────────────────
    mcp_connection_timeout: int = 30
    mcp_read_timeout: int = 60

    # ── 嵌入 / 向量（V3 启用）──
    # embedding_model: str = "BAAI/bge-small-zh-v1.5"
    # qdrant_host: str = "localhost"
    # qdrant_port: int = 6333

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        """从环境变量加载配置。"""
        return cls(
            runtime_host=os.getenv("RUNTIME_HOST", "0.0.0.0"),
            runtime_port=int(os.getenv("RUNTIME_PORT", "8000")),
            runtime_debug=os.getenv("RUNTIME_DEBUG", "").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            default_model_provider=os.getenv("DEFAULT_MODEL_PROVIDER", "openai"),
            default_model_name=os.getenv("DEFAULT_MODEL_NAME", "gpt-4o-mini"),
            default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "4096")),
            backend_base_url=os.getenv("BACKEND_BASE_URL", "http://localhost:8099"),
            react_max_steps=int(os.getenv("REACT_MAX_STEPS", "10")),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD", ""),
            redis_wm_db=int(os.getenv("REDIS_WM_DB", "1")),
            redis_wm_ttl=int(os.getenv("REDIS_WM_TTL", "3600")),
            redis_wm_capacity=int(os.getenv("REDIS_WM_CAPACITY", "100")),
            mcp_connection_timeout=int(os.getenv("MCP_CONNECTION_TIMEOUT", "30")),
            mcp_read_timeout=int(os.getenv("MCP_READ_TIMEOUT", "60")),
        )


# 全局单例（懒加载，首次访问时初始化）
_config: Optional[RuntimeConfig] = None


def get_config() -> RuntimeConfig:
    """获取全局配置单例。"""
    global _config
    if _config is None:
        _config = RuntimeConfig.from_env()
    return _config


def reload_config() -> RuntimeConfig:
    """重新加载配置（主要用于测试/热更新场景）。"""
    global _config
    _config = RuntimeConfig.from_env()
    return _config
