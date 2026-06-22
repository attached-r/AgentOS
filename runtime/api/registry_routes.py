"""
Agent 注册管理端点。

后端通过以下接口管理运行时的 Agent 配置：
  GET  /runtime/agents              — 查看所有已注册 Agent（调试/监控用）
  POST /runtime/agents/sync         — 全量同步（仅启动时调用）
  POST /runtime/agents/upsert       — 增量新增/更新单个 Agent
  DELETE /runtime/agents/{agent_id} — 增量删除单个 Agent

V2 优化：
  - 启动时全量同步保证一致性
  - CRUD 操作改为增量 upsert/delete，避免每次全量推送
"""
from fastapi import APIRouter

from agents.registry import AgentConfig, agent_registry

router = APIRouter()


@router.get("/")
async def list_agents():
    """列出所有已注册的 Agent 配置。"""
    return agent_registry.list_all_dicts()


@router.post("/sync")
async def sync_agents(agents: list[AgentConfig]):
    """
    全量同步 Agent 配置（仅启动时调用）。

    由后端 ApplicationReadyEvent 触发，保证运行时与数据库一致。
    """
    agent_registry.sync_all(agents)
    return {"status": "ok", "count": agent_registry.count()}


@router.post("/upsert")
async def upsert_agent(agent: AgentConfig):
    """
    增量新增或更新单个 Agent 配置。

    由后端在 Agent 创建/更新时调用，避免全量推送。
    """
    agent_registry.add_or_update(agent)
    return {"status": "ok"}


@router.delete("/{agent_id}")
async def remove_agent(agent_id: int):
    """
    增量删除单个 Agent 配置。

    由后端在 Agent 删除时调用。
    """
    removed = agent_registry.remove(agent_id)
    return {"status": "ok", "removed": removed}
