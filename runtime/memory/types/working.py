"""
WorkingMemory —— 工作记忆（短期记忆）。

V2 简化实现：
  - 内存存储（List[MemoryItem]）
  - TTL 过期：超过指定时间的记忆自动失效
  - 容量限制：超过容量时淘汰最不重要 + 最旧的记忆
  - 检索方式：关键词匹配 + 重要性排序（V2 简化为关键词包含匹配）
  - V3 引入向量检索 + 语义匹配

工作记忆用于当前会话的上下文保持，
不跨会话持久化，会话结束后自动释放。
"""
import time
from typing import List, Optional

from memory.base import BaseMemory, MemoryItem


# ---------------------------------------------------------------------------
# WorkingMemory
# ---------------------------------------------------------------------------

class WorkingMemory(BaseMemory):
    """
    工作记忆 —— 内存存储，TTL 过期。

    特点：
      - 纯内存，速度快
      - 自动过期淘汰
      - 容量有限（默认 100 条）
      - 检索基于关键词匹配 + 重要性排序
    """

    def __init__(self, ttl: int = 3600, capacity: int = 100):
        """
        Args:
            ttl:      记忆 TTL（秒），超过此时间的记忆将在检索时被忽略。
                      默认 3600（1 小时）。
            capacity: 存储容量上限，超过时淘汰最不重要 + 最旧的记忆。
                      默认 100 条。
        """
        self._items: List[MemoryItem] = []
        self._timestamps: List[float] = []  # 与 _items 一一对应，记录添加时间
        self.ttl = ttl
        self.capacity = capacity

    async def add(self, item: MemoryItem) -> int:
        """
        添加一条工作记忆。

        自动设置创建时间（如果未设置），
        并在添加后检查容量限制。

        Args:
            item: 记忆项

        Returns:
            记忆在列表中的索引 + 1（作为简易 ID）
        """
        if not item.created_at:
            item.created_at = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime()
            )

        self._items.append(item)
        self._timestamps.append(time.time())

        # 容量检查
        self._enforce_capacity()

        return len(self._items)

    async def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """
        搜索工作记忆。

        V2 简化：关键词包含匹配 + 重要性排序。
        先清理过期记忆，再匹配关键词，最后按重要性排序返回 top-k。

        Args:
            query: 搜索关键词
            limit: 返回条数上限

        Returns:
            匹配的记忆项列表（按重要性降序）
        """
        self._evict_expired()

        query_lower = query.lower()
        matched = []

        for item in self._items:
            if query_lower in item.content.lower():
                matched.append(item)

        # 按重要性降序排列
        matched.sort(key=lambda x: x.importance, reverse=True)

        return matched[:limit]

    async def get(self, item_id: int) -> Optional[MemoryItem]:
        """
        根据 ID 获取单条工作记忆。

        Args:
            item_id: 记忆 ID（索引 + 1）

        Returns:
            MemoryItem 或 None
        """
        idx = item_id - 1
        if 0 <= idx < len(self._items):
            return self._items[idx]
        return None

    async def delete(self, item_id: int) -> bool:
        """
        删除指定 ID 的工作记忆。

        Args:
            item_id: 记忆 ID

        Returns:
            是否删除成功
        """
        idx = item_id - 1
        if 0 <= idx < len(self._items):
            self._items.pop(idx)
            self._timestamps.pop(idx)
            return True
        return False

    async def clear(self) -> None:
        """清空所有工作记忆。"""
        self._items.clear()
        self._timestamps.clear()

    async def count(self) -> int:
        """返回当前工作记忆数量（已排除过期项）。"""
        self._evict_expired()
        return len(self._items)

    # ── 内部方法 ──────────────────────────────────────────────────

    def _evict_expired(self) -> None:
        """
        淘汰过期的工作记忆。

        遍历所有记忆，移除超过 TTL 的项。
        """
        now = time.time()
        keep_items = []
        keep_timestamps = []

        for item, ts in zip(self._items, self._timestamps):
            if now - ts <= self.ttl:
                keep_items.append(item)
                keep_timestamps.append(ts)

        self._items = keep_items
        self._timestamps = keep_timestamps

    def _enforce_capacity(self) -> None:
        """
        强制执行容量限制。

        超过容量时，按（重要性升序，时间升序）排序，
        移除最不重要且最旧的记忆，直到低于容量。
        """
        if len(self._items) <= self.capacity:
            return

        # 创建 (item, timestamp) 对，按重要性升序 + 时间升序排序
        paired = list(zip(self._items, self._timestamps))
        paired.sort(key=lambda x: (x[0].importance, x[1]))

        # 保留最近 + 最重要的 capacity 条
        keep = paired[-self.capacity:]
        self._items = [p[0] for p in keep]
        self._timestamps = [p[1] for p in keep]
