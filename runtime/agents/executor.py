import os
from openai import AsyncOpenAI


# Provider registry: maps provider name to base_url and API key env var
PROVIDER_CONFIG = {
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
        "api_key_env": None,
    },
    "modelscope": {
        "base_url": "https://api-inference.modelscope.cn/v1/",
        "api_key_env": "MODELSCOPE_API_KEY",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "api_key_env": "ZHIPU_API_KEY",
    },
}


class AgentExecutor:
    """Single-agent executor — V1 only does: user msg -> LLM -> response."""

    def __init__(self, agent_config: dict):
        provider = agent_config.get("model_provider", "openai")
        provider_cfg = PROVIDER_CONFIG.get(provider)

        # Resolve base_url: config override > provider default
        base_url = agent_config.get("base_url")
        if not base_url and provider_cfg:
            base_url = provider_cfg["base_url"]
        base_url = base_url or "https://api.openai.com/v1"

        # Resolve api_key: config > provider env var > generic LLM_API_KEY
        api_key = agent_config.get("api_key")
        if not api_key:
            env_var = provider_cfg.get("api_key_env") if provider_cfg else None
            if env_var:
                api_key = os.getenv(env_var)
            if not api_key:
                api_key = os.getenv("LLM_API_KEY")

        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.system_prompt = agent_config.get("system_prompt", "")
        self.model = agent_config.get("model_name", "gpt-4o-mini")
        self.temperature = agent_config.get("temperature", 0.7)
        self.max_tokens = agent_config.get("max_tokens", 4096)

    async def invoke(self, messages: list[dict]) -> dict:
        """Call the LLM and return response content + token usage."""
        full_messages = list(messages)
        if self.system_prompt:
            full_messages.insert(0, {"role": "system", "content": self.system_prompt})

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}") from e

        return {
            "content": resp.choices[0].message.content,
            "usage": {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            },
        }
