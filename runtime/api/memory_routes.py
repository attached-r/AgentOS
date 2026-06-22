"""
记忆端点 —— V2 新增。

提供 Runtime 内部的记忆读写接口，供后端查询和保存 Agent 记忆。
V2 简化方案：Runtime 不直接连接数据库，通过 httpx 回调后端 API 实现持久化。

端点：
  - GET  /runtime/agents/{agent_id}/memories — 查询 Agent 记忆
  - POST /runtime/memory/save                — 保存记忆项
"""
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import get_config

router = APIRouter()


# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------

class SaveMemoryRequest(BaseModel):
    """保存记忆请求体。"""
    agent_id: int
    user_id: int = 0
    memory_type: str = "episodic"            # working / episodic
    content: str
    importance: float = 0.5
    metadata: Optional[Dict[str, Any]] = None


class MemoryItemResponse(BaseModel):
    """记忆项响应模型。"""
    id: Optional[int] = None
    agent_id: int = 0
    user_id: int = 0
    memory_type: str = "working"
    content: str = ""
    importance: float = 0.5
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _get_backend_url() -> str:
    """获取后端 API 基础 URL。"""
    return get_config().backend_base_url


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.get("/agents/{agent_id}/memories", response_model=List[MemoryItemResponse])
async def get_memories(
    agent_id: int,
    memory_type: Optional[str] = None,
    limit: int = 20,
):
    """
    查询 Agent 的长期记忆。

    通过 httpx 回调后端 API（/api/agents/{agent_id}/memories）获取记忆列表。
    V2 简化：依赖后端 PostgreSQL 存储，Runtime 不直接连数据库。

    Args:
        agent_id:    Agent ID
        memory_type: 记忆类型筛选（working / episodic，可选）
        limit:       返回条数上限

    Returns:
        记忆项列表

    Raises:
        502: 后端 API 调用失败
    """
    try:
        backend_url = _get_backend_url()
        params: Dict[str, Any] = {"page": 1, "size": limit}
        if memory_type:
            params["memory_type"] = memory_type

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{backend_url}/api/agents/{agent_id}/memories",
                params=params,
            )

            if resp.status_code == 200:
                data = resp.json()
                # 支持分页和非分页两种后端返回格式
                records = data.get("records", data) if isinstance(data, dict) else data
                return [MemoryItemResponse(**item) for item in records]

            return []

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"后端 API 调用失败: {e}")


@router.post("/memory/save")
async def save_memory(req: SaveMemoryRequest):
    """
    保存记忆项。

    将重要信息持久化到后端数据库（通过 httpx 回调后端 API）。
    由 MemoryManager 在对话过程中自动调用，或由用户手动触发。

    Args:
        req: 保存记忆请求体

    Returns:
        保存结果

    Raises:
        502: 后端 API 调用失败
    """
    try:
        backend_url = _get_backend_url()

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{backend_url}/api/agents/{req.agent_id}/memories",
                json=req.model_dump(exclude_none=True),
            )

            if resp.status_code == 200:
                return {"status": "ok", "detail": "记忆已保存"}
            else:
                return {"status": "error", "detail": f"后端返回: {resp.status_code}"}

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"后端 API 调用失败: {e}")
