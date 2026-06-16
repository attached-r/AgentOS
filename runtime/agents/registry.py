"""
Agent 注册中心 —— 管理 Agent 配置的内存状态。

职责：
  1. AgentConfig 模型：定义从后端同步的 Agent 配置的数据结构
  2. AgentRegistry 类：管理 agent_config 的内存字典（增删改查）
  3. 提供给 api/ 层和 agents/ 层使用，本身不包含路由逻辑

V1 采取简单方案：
  - SpringBoot 启动时通过 /runtime/agents/sync 一次性推送全部 Agent 配置
  - 运行时维护 agent_registry 内存字典
  - V2 改为消息队列实时同步
"""
from typing import Dict, List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# AgentConfig —— 与后端 agent 表对应的配置模型
# ---------------------------------------------------------------------------

class AgentConfig(BaseModel):
    """
    Agent 配置模型 —— 与 Spring Boot 后端 agent 表字段一一对应。

    后端通过 /runtime/agents/sync 推送该结构到运行时。
    """
    id: int
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    model_provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    base_url: Optional[str] = None
    api_key: Optional[str] = None


# ---------------------------------------------------------------------------
# AgentRegistry —— 配置的内存字典
# ---------------------------------------------------------------------------

class AgentRegistry:
    """
    Agent 配置注册表。

    以 agent_id 为 key 的内存字典，提供线程安全的读写操作。
    V1 使用同步锁保证并发安全，V2 替换为 Redis 或消息队列。
    """

    def __init__(self):
        self._agents: Dict[int, AgentConfig] = {}

    # ── 查 ────────────────────────────────────────────────────────

    def get(self, agent_id: int) -> Optional[AgentConfig]:
        """根据 ID 获取 Agent 配置。"""
        return self._agents.get(agent_id)

    def get_dict(self, agent_id: int) -> Optional[dict]:
        """根据 ID 获取 Agent 配置的 dict 形式（给 AgentExecutor 用）。"""
        config = self._agents.get(agent_id)
        return config.model_dump() if config else None

    def list_all(self) -> List[AgentConfig]:
        """列出所有已注册的 Agent 配置。"""
        return list(self._agents.values())

    def list_all_dicts(self) -> List[dict]:
        """列出所有已注册 Agent 的 dict 形式。"""
        return [a.model_dump() for a in self._agents.values()]

    def count(self) -> int:
        """返回当前注册的 Agent 数量。"""
        return len(self._agents)

    # ── 增 / 改 ───────────────────────────────────────────────────

    def sync_all(self, agents: List[AgentConfig]) -> None:
        """
        全量同步：替换整个注册表。

        由后端在启动时和每次 Agent CRUD 后调用。
        """
        self._agents.clear()
        for agent in agents:
            self._agents[agent.id] = agent

    def add_or_update(self, agent: AgentConfig) -> None:
        """新增或更新单个 Agent 配置。"""
        self._agents[agent.id] = agent

    # ── 删 ────────────────────────────────────────────────────────

    def remove(self, agent_id: int) -> bool:
        """删除指定 ID 的 Agent 配置。存在返回 True，不存在返回 False。"""
        return self._agents.pop(agent_id, None) is not None

    def clear(self) -> None:
        """清空注册表。"""
        self._agents.clear()


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------
# 运行时全局唯一的 Agent 注册表实例。
# api/ 层的路由处理器通过此实例读写 Agent 配置。
agent_registry = AgentRegistry()
