"""
EpisodicMemory —— 情景记忆（长期记忆，跨会话持久化）。

V2 简化实现：
  - 不直接连接数据库，通过 httpx 回调 SpringBoot 后端 API 实现持久化
  - 后端收到请求后写入 PostgreSQL（agent_memory 表）
  - 检索时也通过后端 API 进行关键词搜索
  - V3 引入 Qdrant 向量检索

与 WorkingMemory 的区别：
  - WorkingMemory：纯内存，当前会话有效，自动过期
  - EpisodicMemory：持久化存储，跨会话有效，需显式保存和检索
"""
from typing import Any, Dict, List, Optional

import httpx

from memory.base import BaseMemory, MemoryItem


# ---------------------------------------------------------------------------
# EpisodicMemory
# ---------------------------------------------------------------------------

class EpisodicMemory(BaseMemory):
    """
    情景记忆 —— 通过后端 API 持久化到 PostgreSQL。

    保存和检索均通过 httpx 回调后端 API 完成。
    Runtime 不直接连接数据库。

    用法：
        memory = EpisodicMemory(backend_url="http://localhost:8080")

        # 保存重要信息
        await memory.add(MemoryItem(
            agent_id=1,
            user_id=1,
            memory_type="episodic",
            content="用户叫张三，是一名 Python 开发者",
            importance=0.8,
        ))

        # 检索记忆
        results = await memory.search("张三")
    """

    def __init__(self, backend_url: str = "http://localhost:8080"):
        """
        Args:
            backend_url: SpringBoot 后端 API 基础 URL
        """
        self.backend_url = backend_url.rstrip("/")

    async def add(self, item: MemoryItem) -> int:
        """
        保存情景记忆到后端数据库。

        通过 POST /api/agents/{agent_id}/memories 回调后端。

        Args:
            item: 要保存的记忆项

        Returns:
            后端返回的记忆 ID（成功时）或 0（失败时）
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.backend_url}/api/agents/{item.agent_id}/memories",
                    json=item.model_dump(exclude_none=True),
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("id", 0)

                return 0

        except httpx.RequestError:
            return 0

    async def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """
        从后端检索情景记忆。

        通过 GET /api/agents/.../memories 回调后端。
        V2 后端使用 PostgreSQL ILIKE 关键词匹配。

        Args:
            query: 搜索关键词
            limit: 返回条数上限

        Returns:
            匹配的记忆项列表
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.backend_url}/api/agents/0/memories",
                    params={"q": query, "size": limit},
                )

                if resp.status_code == 200:
                    data = resp.json()
                    records = data.get("records", data) if isinstance(data, dict) else data
                    return [MemoryItem(**item) for item in records]

                return []

        except httpx.RequestError:
            return []

    async def get(self, item_id: int, agent_id: int = 0) -> Optional[MemoryItem]:
        """
        获取单条情景记忆。

        V2 修复：原路径 /api/memories/{item_id} 在后端不存在，
        改为通过列表接口带 id 参数查询。

        Args:
            item_id:   记忆 ID
            agent_id:  Agent ID（用于构造后端路径）

        Returns:
            MemoryItem 或 None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.backend_url}/api/agents/{agent_id}/memories",
                    params={"id": item_id, "size": 1},
                )

                if resp.status_code == 200:
                    data = resp.json()
                    records = data.get("records", data) if isinstance(data, dict) else data
                    if records:
                        return MemoryItem(**records[0])

                return None

        except httpx.RequestError:
            return None

    async def delete(self, item_id: int, agent_id: int = 0) -> bool:
        """
        删除情景记忆。

        V2 修复：原路径 /api/memories/{item_id} 在后端不存在，
        后端实际路径为 /api/agents/{agent_id}/memories/{memId}。

        Args:
            item_id:  记忆 ID
            agent_id: Agent ID（后端需要此参数校验属主）

        Returns:
            是否删除成功
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.delete(
                    f"{self.backend_url}/api/agents/{agent_id}/memories/{item_id}",
                )
                return resp.status_code in (200, 204)

        except httpx.RequestError:
            return False

    async def clear(self) -> None:
        """
        清空情景记忆。

        V2 简化：仅记录日志，不实现批量清空。
        生产环境中应通过后端 API 按 agent_id + user_id 清空。
        """
        # V2 暂不实现批量清空，避免误操作
        pass

    async def count(self) -> int:
        """
        返回情景记忆总数。

        通过后端 API 查询 agent 的记忆数量。
        V2 简化：返回 0（需要通过后端分页接口统计）。
        """
        return 0
