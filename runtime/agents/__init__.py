# runtime/agents — Agent 实现层
# 包含所有 Agent 执行策略的实现和全局注册表。
# 依赖 core/ 层提供的基础组件，被 api/ 层调用。

from .registry import AgentConfig, AgentRegistry, agent_registry
from .simple_agent import SimpleAgent

__all__ = [
    "AgentConfig",
    "AgentRegistry",
    "agent_registry",
    "SimpleAgent",
]
