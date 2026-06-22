"""
RAG Pipeline —— 检索增强生成管线（V2 MVP）。

V2 简化方案：
  - 文档切片后直接通过后端 API 存入 PostgreSQL
  - 检索时用关键词匹配（后端 ILIKE / tsvector）
  - 不做向量检索（V3 引入 Qdrant）
  - 不做重排序（V3 引入）

流程：
  1. Index: 文档分块 → POST 后端 API 入库
  2. Retrieve: 用户查询 → GET 后端 API 搜索 → 返回 Top-K Chunk
  3. Generate: 检索结果拼入 system prompt → LLM 增强生成

用法：
    pipeline = RAGPipeline(backend_url="http://localhost:8080")

    # 检索
    chunks = await pipeline.retrieve("AgentOS 的核心功能是什么？", agent_id=1)

    # 构建上下文
    context = pipeline.build_context(chunks)

    # 在 system prompt 中注入 context 后调用 LLM
    prompt = f"基于以下信息回答问题：\n{context}\n\n问题：..."
"""
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional

import httpx

from rag.document import Chunk, ChunkConfig


# ---------------------------------------------------------------------------
# RAGPipeline
# ---------------------------------------------------------------------------

class RAGPipeline:
    """
    检索增强生成管线。

    提供文档索引、检索、上下文构建的端到端能力。
    V2 实现 MVP 版本，V3 升级为向量检索 + 重排序。

    V2 检索策略：
      - 优先：通过后端 API 进行 ILIKE / tsvector 搜索
      - 降级：本地关键词匹配（当后端不可用时）
    """

    def __init__(self, backend_url: str = "http://localhost:8080"):
        """
        Args:
            backend_url: SpringBoot 后端 API 基础 URL
        """
        self.backend_url = backend_url.rstrip("/")
        self.chunk_config = ChunkConfig()

    # ── 检索 ──────────────────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        agent_id: Optional[int] = None,
        top_k: int = 3,
    ) -> List[Chunk]:
        """
        检索与查询相关的知识库片段。

        优先通过后端 API 搜索（PostgreSQL ILIKE），
        后端不可用时降级为本地关键词匹配。

        Args:
            query:    用户查询
            agent_id: 限定 Agent 的知识库（None = 搜索全部）
            top_k:    返回数量上限

        Returns:
            相关的 Chunk 列表（按相关度降序）
        """
        if not query or not query.strip():
            return []

        # 优先：后端 API 搜索
        chunks = await self._backend_search(query, agent_id, top_k)
        if chunks:
            return chunks

        # 降级：本地关键词匹配（V2 简化）
        return self._local_search(query, top_k)

    # ── 上下文构建 ────────────────────────────────────────────────

    def build_context(self, chunks: List[Chunk], max_length: int = 2000) -> str:
        """
        将检索结果拼装为 LLM 友好的上下文文本。

        Args:
            chunks:      检索到的文档片段
            max_length:  上下文最大字符数

        Returns:
            格式化后的上下文字符串
        """
        if not chunks:
            return ""

        parts: List[str] = ["以下是相关知识库内容：\n"]

        total_length = len(parts[0])

        for i, chunk in enumerate(chunks, 1):
            header = f"[{i}] "
            if chunk.title:
                header += f"（来自：{chunk.title}）"
            header += "\n"

            entry = f"{header}{chunk.content}\n\n"

            if total_length + len(entry) > max_length:
                # 超长截断
                remaining = max_length - total_length
                if remaining > 50:  # 至少留 50 字符才添加
                    parts.append(entry[:remaining])
                break

            parts.append(entry)
            total_length += len(entry)

        return "".join(parts)

    # ── 文档分块 ──────────────────────────────────────────────────

    def split_document(self, content: str, title: str = "") -> List[Chunk]:
        """
        将文档内容分割为 Chunk 列表。

        使用固定大小的重叠分块策略：
          1. 按优先级尝试分隔符分割
          2. 超出 chunk_size 的块继续递归分割
          3. 块间保留 chunk_overlap 的重叠字符

        Args:
            content: 文档原始内容
            title:   文档标题（可选，会注入到每个 Chunk）

        Returns:
            Chunk 列表
        """
        if not content:
            return []

        return self._split_text(
            text=content,
            title=title,
            chunk_size=self.chunk_config.chunk_size,
            overlap=self.chunk_config.chunk_overlap,
        )

    # ── 内部方法 ──────────────────────────────────────────────────

    async def _backend_search(
        self,
        query: str,
        agent_id: Optional[int] = None,
        top_k: int = 3,
    ) -> List[Chunk]:
        """
        通过后端 API 搜索知识库。

        GET /api/knowledge/docs/search?q=xxx&agent_id=xxx&top_k=xxx

        Returns:
            Chunk 列表，后端不可用时返回空列表
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params: Dict[str, Any] = {"q": query, "top_k": top_k}
                if agent_id is not None:
                    params["agent_id"] = agent_id

                resp = await client.get(
                    f"{self.backend_url}/api/knowledge/docs/search",
                    params=params,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        return [Chunk(**c) for c in data]
                    return [Chunk(**data)] if data else []

                return []

        except httpx.RequestError:
            return []

    def _local_search(self, query: str, top_k: int = 3) -> List[Chunk]:
        """
        本地关键词匹配检索。

        V2 降级方案：仅作简单关键词匹配，不依赖后端。
        适用于后端 API 不可用时的兜底场景。

        Args:
            query:  搜索关键词
            top_k: 返回数量上限

        Returns:
            匹配的 Chunk 列表（V2 简化返回空列表）
        """
        # V2 简化为空实现 —— 本地检索依赖本地文档缓存，
        # V2 暂不实现本地文档缓存，返回空。
        return []

    def _split_text(
        self,
        text: str,
        title: str = "",
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> List[Chunk]:
        """
        递归分割文本。

        Args:
            text:       要分割的文本
            title:      文档标题
            chunk_size: 每块字符上限
            overlap:    块间重叠字符数

        Returns:
            Chunk 列表
        """
        if len(text) <= chunk_size:
            return [Chunk(doc_id=0, content=text, title=title, index=0)]

        chunks: List[Chunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = start + chunk_size

            if end >= len(text):
                # 最后一块
                chunks.append(Chunk(
                    doc_id=0,
                    content=text[start:],
                    title=title,
                    index=index,
                ))
                break

            # 在前一隔符处断开（避免断在词中间）
            cut_pos = self._find_split_position(text, start, end)

            chunks.append(Chunk(
                doc_id=0,
                content=text[start:cut_pos],
                title=title,
                index=index,
            ))

            # 下一块从 cut_pos - overlap 开始（重叠）
            start = cut_pos - overlap
            index += 1

            # 防止死循环：如果 cut_pos <= start，强制前移
            if start <= cut_pos - overlap:
                start = cut_pos - overlap
            if start >= len(text):
                break

        return chunks

    def _find_split_position(self, text: str, start: int, end: int) -> int:
        """
        在 [start, end] 范围内寻找最佳分割位置。

        按分隔符优先级在结束位置附近寻找换行符/句号/逗号等。

        Args:
            text:  完整文本
            start: 起始位置
            end:   结束位置（chunk_size 边界）

        Returns:
            最佳分割位置
        """
        # 从 end 向前搜索分隔符
        search_start = max(start, end - 100)  # 最多向前 100 字符

        for sep in self.chunk_config.separators:
            pos = text.rfind(sep, search_start, end)
            if pos != -1:
                return pos + len(sep)

        # 没有合适的分隔符，在 end 处强制分割
        return end

    # ── 数据统计 ──────────────────────────────────────────────────

    def estimate_chunk_count(self, content: str) -> int:
        """
        估算文档分块数量。

        Args:
            content: 文档内容

        Returns:
            预估的分块数
        """
        if not content:
            return 0
        return max(1, math.ceil(len(content) / self.chunk_config.chunk_size))
