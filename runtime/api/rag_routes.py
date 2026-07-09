"""
RAG 路由 —— 文档分块端点。

后端 triggerIndex 时调用此接口让 Runtime 做文档分块。
Runtime 的 RAGPipeline.split_document() 是分块逻辑的唯一实现，
后端不重复实现分块算法。
"""
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from rag.pipeline import RAGPipeline
from config import get_config

router = APIRouter()


# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------

class ChunkRequest(BaseModel):
    """分块请求体。"""
    content: str
    title: str = ""


class ChunkItem(BaseModel):
    """单个分块结果。"""
    content: str
    index: int
    title: str


class ChunkResponse(BaseModel):
    """分块响应体。"""
    chunks: List[ChunkItem]


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/rag/chunk", response_model=ChunkResponse)
async def chunk_document(req: ChunkRequest):
    """
    对文档内容做分块处理。

    调用 RAGPipeline.split_document() 将 content 切割为多个 Chunk，
    供后端存入 knowledge_chunk 表。

    Args:
        req: ChunkRequest { content, title }

    Returns:
        ChunkResponse { chunks: [{ content, index, title }] }
    """
    pipeline = RAGPipeline(backend_url=get_config().backend_base_url)
    chunks = pipeline.split_document(content=req.content, title=req.title)

    return ChunkResponse(
        chunks=[
            ChunkItem(content=c.content, index=c.index, title=c.title)
            for c in chunks
        ],
    )
