"""
运行时配置 —— 从环境变量加载所有可配置项。

集中管理所有配置项，而不是散落在各个模块中。
所有配置项都有默认值，通过 `.env` 文件或环境变量覆盖。
"""
import os
from dataclasses import dataclass, field
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
    runtime_port: int = 8001
    runtime_debug: bool = False
    runtime_title: str = "AgentOS Runtime"
    log_level: str = "INFO"

    # ── LLM 默认值 ────────────────────────────────────────────────
    default_model_provider: str = "openai"
    default_model_name: str = "gpt-4o-mini"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        """从环境变量加载配置。"""
        return cls(
            runtime_host=os.getenv("RUNTIME_HOST", "0.0.0.0"),
            runtime_port=int(os.getenv("RUNTIME_PORT", "8001")),
            runtime_debug=os.getenv("RUNTIME_DEBUG", "").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            default_model_provider=os.getenv("DEFAULT_MODEL_PROVIDER", "openai"),
            default_model_name=os.getenv("DEFAULT_MODEL_NAME", "gpt-4o-mini"),
            default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "4096")),
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
