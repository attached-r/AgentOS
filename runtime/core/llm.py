"""
LLM 客户端 —— 多供应商 LLM 调用抽象层。

功能：
  1. 通过 PROVIDER_CONFIG 注册表管理不同供应商的 base_url / API Key 策略
  2. 自动从环境变量解析凭据（供应商专用变量 → 通用 LLM_API_KEY / LLM_BASE_URL）
  3. 统一 invoke() 接口，返回结构化结果（content + usage）
  4. 为 V2 流式预留 stream_invoke() 接口

用法：
    client = LLMClient(model_provider="openai", model_name="gpt-4o-mini")
    result = await client.invoke(messages=[...], system_prompt="...")
"""
import os
from typing import Dict, List, Optional

from openai import AsyncOpenAI  #异步 OpenAI 客户端


# ---------------------------------------------------------------------------
# Provider 注册表 —— 添加新供应商只需在此注册
# ---------------------------------------------------------------------------
PROVIDER_CONFIG: Dict[str, Dict] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1/",
        "api_key_env": None,          # Ollama 不需要 API Key
    },
    "modelscope": {
        "base_url": "https://api-inference.modelscope.cn/v1/",
        "api_key_env": "MODELSCOPE_API_KEY",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "api_key_env": "ZHIPU_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
}


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

class LLMClient:
    """
    多供应商 LLM 客户端。

    支持任何兼容 OpenAI Chat Completions API 的服务。
    通过 PROVIDER_CONFIG 注册表管理不同供应商的默认配置。

    使用方式：
        # 方式一：指定 provider（推荐）
        client = LLMClient(model_provider="openai", model_name="gpt-4o-mini")

        # 方式二：从 agent_config dict 直接构造
        client = LLMClient.from_agent_config(agent_config)
    """

    def __init__(
        self,
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 解析最终使用的 base_url 和 api_key
        resolved_url, resolved_key = self._resolve_credentials(
            provider=model_provider,
            api_key=api_key,
            base_url=base_url,
        )
        self.client = AsyncOpenAI(base_url=resolved_url, api_key=resolved_key)

    @classmethod  # 类方法，用于从 agent_config 构造 LLMClient
    def from_agent_config(cls, config: dict) -> "LLMClient":
        """从 agent_registry 中的配置 dict 构造 LLMClient。"""
        provider = config.get("model_provider", "openai")
        return cls(
            model_provider=provider,
            model_name=config.get("model_name", "gpt-4o-mini"),
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 4096),
        )

    # ------------------------------------------------------------------
    # 凭据解析
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_credentials(
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> tuple:
        """
        根据 provider 解析最终的 (base_url, api_key)。

        优先级：
          1. 调用时显式传入的值
          2. 该供应商专用的环境变量（如 OPENAI_API_KEY）
          3. 通用环境变量 LLM_API_KEY / LLM_BASE_URL
          4. PROVIDER_CONFIG 注册表中的默认 base_url
        """
        cfg = PROVIDER_CONFIG.get(provider)

        if cfg is None:
            # 未知 provider —— 直接用通用变量或原始值
            return (
                base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1",
                api_key or os.getenv("LLM_API_KEY") or "",
            )

        # 供应商专用环境变量
        env_key = os.getenv(cfg["api_key_env"]) if cfg.get("api_key_env") else None

        resolved_key = api_key or env_key or os.getenv("LLM_API_KEY") or ""
        resolved_url = base_url or os.getenv("LLM_BASE_URL") or cfg["base_url"]

        return resolved_url, resolved_key

    # ------------------------------------------------------------------
    # 核心调用方法
    # ------------------------------------------------------------------

    async def invoke(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> Dict:
        """
        调用 LLM，返回结构化的响应内容 + token 用量。

        Args:
            messages:  格式为 [{"role": "user", "content": "..."}] 的历史消息
            system_prompt: 可选的 system prompt，会插入到消息列表最前面

        Returns:
            {
                "content": "LLM 回复文本",
                "usage": {
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int,
                }
            }

        Raises:
            RuntimeError: LLM API 调用失败时抛出
        """
        full_messages = list(messages)
        if system_prompt:
            full_messages.insert(0, {"role": "system", "content": system_prompt})

        try:  #? 异步调用 LLM API，处理异常
            resp = await self.client.chat.completions.create( 
                model=self.model_name,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            raise RuntimeError(f"LLM API 调用失败: {e}") from e

        return {
            "content": resp.choices[0].message.content or "",
            "usage": {
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "total_tokens": resp.usage.total_tokens if resp.usage else 0,
            },
        }
