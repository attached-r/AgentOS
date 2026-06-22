"""
文档模型 —— Document 和 Chunk 的数据结构。

Document 对应后端 knowledge_doc 表的一条记录。
Chunk 是 Document 的分块，用于检索粒度控制。
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Document —— 知识库文档
# ---------------------------------------------------------------------------

class Document(BaseModel):
    """
    知识库文档模型。

    对应后端 knowledge_doc 表的字段结构。
    文档可以属于某个 Agent（agent_id 不为空）或全局共享（agent_id 为空）。
    """
    id: Optional[int] = None
    agent_id: Optional[int] = None               # NULL = 全局文档
    title: str = ""
    content: str = ""                            # 文档原始内容
    source: str = "manual"                       # manual / upload / web
    chunk_count: int = 0                         # 分块数量
    embedding_status: int = 0                    # 0:未索引 1:索引中 2:已索引
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典。"""
        return self.model_dump(exclude_none=True)


# ---------------------------------------------------------------------------
# Chunk —— 文档分块
# ---------------------------------------------------------------------------

class Chunk(BaseModel):
    """
    文档分块模型。

    用于 RAG 检索的最小单位。
    每个 Chunk 从 Document 中分割而来，包含原文的一个片段。
    """
    doc_id: int = 0                              # 所属文档 ID
    content: str = ""                            # 分块内容
    index: int = 0                               # 块序号（在文档中的位置）
    title: str = ""                              # 所属文档标题（冗余，方便展示）
    score: float = 0.0                           # 检索相关度分数（0.0 ~ 1.0）

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


# ---------------------------------------------------------------------------
# ChunkConfig —— 分块配置
# ---------------------------------------------------------------------------

class ChunkConfig:
    """
    文档分块配置。

    V2 使用固定大小的重叠分块策略。
    V3 引入语义分块（按段落/标题分割）。
    """
    chunk_size: int = 512                        # 每块字符数
    chunk_overlap: int = 50                      # 块间重叠字符数
    separators: List[str] = ["\n\n", "\n", "。", "！", "？", "；", "，", " "]  # 分割符优先级
