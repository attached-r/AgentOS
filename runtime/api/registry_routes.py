"""
Agent 注册管理端点。

后端通过以下接口管理运行时的 Agent 配置：
  GET  /runtime/agents       — 查看所有已注册 Agent（调试/监控用）
  POST /runtime/agents/sync  — 全量同步 Agent 配置（后端启动 / CRUD 后调用）

V1 简化方案：
  - 后端启动时一次性推送
  - Agent CRUD 后增量推送（可选）
  - V2 改为消息队列实时同步
"""
from fastapi import APIRouter

from agents.registry import AgentConfig, agent_registry

router = APIRouter()


@router.get("/")
async def list_agents():
    """
    列出所有已注册的 Agent 配置。

    用于调试和监控，返回注册表中所有 Agent 的完整配置列表。
    """
    return agent_registry.list_all_dicts()


@router.post("/sync")
async def sync_agents(agents: list[AgentConfig]):
    """
    全量同步 Agent 配置。

    由 Spring Boot 后端在以下时机调用：
      1. 应用启动完成后（ApplicationReadyEvent）
      2. Agent 创建 / 更新 / 删除后

    替换整个注册表内容，保证运行时与后端状态一致。
    """
    agent_registry.sync_all(agents)
    return {"status": "ok", "count": agent_registry.count()}
