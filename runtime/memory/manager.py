"""
MemoryManager —— 记忆管理器（V2 简化版）。

统一入口，管理所有类型的记忆操作。
V2 只实现两级记忆：
  1. 工作记忆（Working）：当前会话的对话摘要，存储在内存中
  2. 情景记忆（Episodic）：跨会话的重要信息，通过后端 API 存到 PostgreSQL

V2 不实现的：
  - 语义记忆（Semantic）：V3
  - 感知记忆（Perceptual）：V4
  - Qdrant 向量检索：V3

用法：
    manager = MemoryManager(backend_url="http://localhost:8080")

    # 保存记忆
    await manager.save(
        content="用户叫张三",
        memory_type="episodic",
        importance=0.8,
        agent_id=1,
        user_id=1,
    )

    # 检索记忆
    results = await manager.search("张三")
"""
from typing import Any, Dict, List, Optional

from memory.base import MemoryConfig, MemoryItem
from memory.types.working import WorkingMemory
from memory.types.episodic import EpisodicMemory

from config import get_config


# ---------------------------------------------------------------------------
# MemoryManager
# ---------------------------------------------------------------------------

class MemoryManager:
    """
    记忆管理器 —— V2 简化版。

    整合工作记忆和情景记忆，提供统一的读写接口。
    自动根据重要性决定记忆的存储层级。
    """

    def __init__(self, backend_url: Optional[str] = None):
        """
        Args:
            backend_url: SpringBoot 后端 API 地址（情景记忆持久化用）。
                         默认从全局配置读取。
        """
        cfg = get_config()
        url = backend_url or cfg.backend_base_url

        self.config = MemoryConfig()
        self.working = WorkingMemory(
            ttl=self.config.working_ttl,
            capacity=self.config.working_capacity,
        )
        self.episodic = EpisodicMemory(backend_url=url)

    async def save(
        self,
        content: str,
        memory_type: str = "working",
        importance: float = 0.5,
        agent_id: int = 0,
        user_id: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        保存一条记忆。

        根据记忆类型和重要性，自动选择合适的存储层级：
          - "working":  存入内存中的工作记忆
          - "episodic": 存入后端持久化存储

        Args:
            content:     记忆内容
            memory_type: 记忆类型（"working" / "episodic"）
            importance:  重要性（0.0 ~ 1.0）
            agent_id:    Agent ID
            user_id:     用户 ID
            metadata:    附加元数据

        Returns:
            记忆 ID
        """
        item = MemoryItem(
            agent_id=agent_id,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            metadata=metadata,
        )

        if memory_type == "working":
            return await self.working.add(item)
        elif memory_type == "episodic":
            return await self.episodic.add(item)
        else:
            # 未知类型，默认存入工作记忆
            return await self.working.add(item)

    async def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5,
        agent_id: int = 0,  # V2 修复：添加 agent_id 参数，传递给 EpisodicMemory.search()
    ) -> List[MemoryItem]:
        """
        跨记忆类型搜索。

        Args:
            query:       搜索关键词
            memory_type: 筛选记忆类型（None = 搜索全部）
            limit:       返回条数上限
            agent_id:    Agent ID（搜索情景记忆时传参限定范围，V2 修复）

        Returns:
            合并后的记忆项列表（按重要性降序排列）
        """
        results: List[MemoryItem] = []

        # 搜索工作记忆
        if memory_type in (None, "working"):
            working_results = await self.working.search(query, limit)
            results.extend(working_results)

        # 搜索情景记忆（V2 修复：传入 agent_id，原硬编码为 0 导致跨用户数据泄漏风险）
        if memory_type in (None, "episodic"):
            episodic_results = await self.episodic.search(query, limit, agent_id=agent_id)
            results.extend(episodic_results)

        # 按重要性降序排列，取 top-k
        results.sort(key=lambda x: x.importance, reverse=True)

        return results[:limit]

    async def consolidate(self) -> int:
        """
        记忆整合：将重要的工作记忆提升为情景记忆。

        模拟人脑睡眠时的记忆巩固过程。
        遍历工作记忆，将重要性高于阈值的项转为情景记忆并持久化。

        Returns:
            提升为情景记忆的数量
        """
        promoted = 0
        threshold = self.config.episodic_importance_threshold

        for item in await self._items_snapshot():
            if item.importance >= threshold:
                item.memory_type = "episodic"
                mem_id = await self.episodic.add(item)
                if mem_id > 0:
                    await self.working.delete(item.id or 0)
                    promoted += 1

        return promoted

    async def clear_working(self) -> None:
        """清空工作记忆。"""
        await self.working.clear()

    async def stats(self) -> Dict[str, Any]:
        """
        返回记忆系统的统计信息。

        Returns:
            {
                "working_count": 工作记忆数量,
                "episodic_count": 情景记忆数量,
                "config": { ... },
            }
        """
        return {
            "working_count": await self.working.count(),
            "episodic_count": await self.episodic.count(),
            "config": self.config.model_dump(),
        }

    # ── 内部方法 ──────────────────────────────────────────────────

    async def _items_snapshot(self) -> List[MemoryItem]:
        """
        获取当前工作记忆的快照。

        用于 consolidate 过程中的遍历，避免在迭代时修改列表。
        V2 修复：原实现引用了不存在的 self._items 属性导致崩溃，
        改为通过 working.search("") 获取全部工作记忆。
        """
        # search("") 匹配所有条目（空字符串是任何内容的子串），
        # 同时会自动清理过期记忆
        return await self.working.search("", limit=self.config.working_capacity)
