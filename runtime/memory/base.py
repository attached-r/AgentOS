"""
记忆基础模块 —— 记忆项模型、配置、存储基类。

定义 V2 记忆系统的核心数据结构：
  - MemoryItem：单条记忆的数据模型
  - BaseMemory：记忆存储的抽象接口
  - MemoryConfig：记忆系统的配置项
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# MemoryItem —— 单条记忆的数据模型
# ---------------------------------------------------------------------------

class MemoryItem(BaseModel):
    """
    记忆项模型。

    对应后端 agent_memory 表的字段结构。
    V2 实现 working 和 episodic 两种记忆类型。
    """
    id: Optional[int] = None                      # 记忆 ID（数据库主键）
    agent_id: int = 0                             # 所属 Agent ID
    user_id: int = 0                              # 所属用户 ID
    memory_type: str = "working"                  # 记忆类型：working / episodic / semantic
    content: str = ""                             # 记忆内容
    importance: float = 0.5                       # 重要性（0.0 ~ 1.0），用于排序和遗忘
    metadata: Optional[Dict[str, Any]] = None     # 附加元数据（JSONB）
    created_at: Optional[str] = None              # 创建时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典。"""
        return self.model_dump(exclude_none=True)


# ---------------------------------------------------------------------------
# MemoryConfig —— 记忆系统配置
# ---------------------------------------------------------------------------

class MemoryConfig(BaseModel):
    """
    记忆系统配置。

    V2 简化版只配置工作记忆的 TTL 和容量。
    """
    # 工作记忆
    working_ttl: int = 3600                       # 工作记忆 TTL（秒），默认 1 小时
    working_capacity: int = 100                   # 工作记忆容量上限

    # 情景记忆
    episodic_importance_threshold: float = 0.3    # 提升为情景记忆的重要性阈值

    # 嵌入
    embedding_model: str = "tfidf"                # 嵌入模型（V2 使用 TF-IDF）


# ---------------------------------------------------------------------------
# BaseMemory —— 记忆存储抽象基类
# ---------------------------------------------------------------------------

class BaseMemory(ABC):
    """
    记忆存储基类。

    定义所有记忆类型的统一接口：
      - add：添加记忆
      - search：搜索记忆
      - get：获取单条记忆
      - delete：删除记忆
      - clear：清空所有记忆
      - count：统计记忆数量
    """

    @abstractmethod
    async def add(self, item: MemoryItem) -> int:
        """添加一条记忆，返回记忆 ID。"""
        ...

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """搜索记忆，返回最相关的 top-k 条。"""
        ...

    @abstractmethod
    async def get(self, item_id: int) -> Optional[MemoryItem]:
        """根据 ID 获取单条记忆。"""
        ...

    @abstractmethod
    async def delete(self, item_id: int) -> bool:
        """删除指定 ID 的记忆。存在且删除成功返回 True。"""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """清空所有记忆。"""
        ...

    @abstractmethod
    async def count(self) -> int:
        """返回记忆总数。"""
        ...
