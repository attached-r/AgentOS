# runtime/core — AgentOS 运行时核心层
# 提供 LLM 客户端抽象、Message 模型、Agent 基类等基础组件。
# 上层 agents/ 和 api/ 依赖本层，本层不依赖任何业务模块。

from .message import Message, messages_to_dicts, dicts_to_messages
from .llm import LLMClient
from .agent import BaseAgent

__all__ = [
    "Message",
    "messages_to_dicts",
    "dicts_to_messages",
    "LLMClient",
    "BaseAgent",
]
