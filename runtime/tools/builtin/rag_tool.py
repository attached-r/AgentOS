"""
RAGTool —— 知识检索工具（内置工具）。

将 RAGPipeline 封装为 Tool，供 Agent 在推理循环中主动调用。
Agent 可通过此工具查询知识库，获取与问题相关的文档片段。

与被动 RAG 注入（invoke_routes.py 中的预先检索）互为补充：
  - 被动注入：每次调用前自动检索相关知识拼入 system prompt（无需 Agent 干预）
  - 主动工具：Agent 在推理过程中按需查询，可针对特定问题深入检索

V2 支持的操作:
  query       检索知识库（关键词 ILIKE 匹配，V3 升级 Qdrant 向量检索）
  ingest_text 将文本导入知识库（V2 简化：直接调用后端 API）

V2 检索策略：
  - 优先：通过后端 API 进行 ILIKE 关键词搜索
  - 降级：本地关键词匹配（当后端不可用时，V2 暂未实现本地缓存）
"""
from typing import Any, Dict

import httpx

from tools.base import Tool
from rag.pipeline import RAGPipeline


class RAGTool(Tool):
    """
    知识检索工具。

    Agent 可通过此工具主动查询知识库，获取与当前问题相关的文档信息。
    也支持将新知识直接导入知识库。

    用法（由 ToolRegistry 自动注册，Agent 通过 function calling 调用）：
      { "action": "query", "query": "AgentOS 的核心功能是什么？" }
      { "action": "ingest_text", "text": "新的知识内容...", "title": "文档标题" }
    """

    def __init__(self, rag: RAGPipeline):
        """
        Args:
            rag: RAGPipeline 实例（全局共享）
        """
        super().__init__(
            name="knowledge_retrieval",
            description=(
                "知识检索工具。用于从知识库中搜索与问题相关的信息，"
                "也可以将新知识导入知识库。"
            ),
        )
        self.rag = rag

    async def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行知识库操作。

        根据 action 参数分发到对应的处理方法。

        Args:
            parameters: 工具参数字典，必须包含 "action" 字段

        Returns:
            操作结果文本
        """
        action = parameters.get("action", "query")
        handler = getattr(self, f"_{action}", None)
        if handler is None:
            return (
                f"未知操作: {action}，支持: "
                f"query/ingest_text"
            )
        return await handler(**parameters)

    def to_openai_schema(self) -> Dict[str, Any]:
        """返回 OpenAI function calling 格式的 schema。"""
        return {
            "type": "function",
            "function": {
                "name": "knowledge_retrieval",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "操作类型",
                            "enum": ["query", "ingest_text"],
                        },
                        "query": {
                            "type": "string",
                            "description": "搜索关键词或自然语言问题（query 操作需要）",
                        },
                        "agent_id": {
                            "type": "integer",
                            "description": "限定搜索的 Agent ID（可选，不传则搜索全部知识库）",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回文档片段数量（可选，默认 3）",
                        },
                        "text": {
                            "type": "string",
                            "description": "要导入的文本内容（ingest_text 操作需要）",
                        },
                        "title": {
                            "type": "string",
                            "description": "文档标题（ingest_text 操作可选）",
                        },
                    },
                    "required": ["action"],
                },
            },
        }

    # ── 操作实现 ──────────────────────────────────────────────────

    async def _query(self, **params) -> str:
        """
        检索知识库。

        V2 使用后端 API 的 ILIKE 关键词匹配，V3 升级 Qdrant 向量检索。

        Args:
            params: query（必填）, agent_id, top_k

        Returns:
            格式化后的检索结果文本（含文档片段和来源信息）
        """
        query_text = params.get("query", "")
        if not query_text:
            return "❌ 查询内容不能为空"

        agent_id = params.get("agent_id")
        top_k = int(params.get("top_k", 3))

        try:
            chunks = await self.rag.retrieve(
                query=query_text,
                agent_id=agent_id,
                top_k=top_k,
            )

            if not chunks:
                return "💡 知识库中未找到相关信息"

            lines = [f"🔍 知识库检索到 {len(chunks)} 个相关片段:\n"]
            for i, chunk in enumerate(chunks, 1):
                lines.append(f"  [{i}] ", )
                if chunk.title:
                    lines.append(f"（来自: {chunk.title}）")
                lines.append(f"\n")
                # 内容截断到 500 字符，避免工具输出过长
                content = chunk.content[:500]
                lines.append(f"      {content}\n\n")

            return "".join(lines)

        except Exception as e:
            return f"❌ 知识库检索失败: {e}"

    async def _ingest_text(self, **params) -> str:
        """
        将文本导入知识库。

        V2 简化实现：直接调用后端 API 创建知识库文档。
        文档会经过分块处理后存储，后续可通过 query 检索到。

        Args:
            params: text（必填）, title（可选）, agent_id（可选）

        Returns:
            导入结果文本
        """
        text = params.get("text", "")
        if not text:
            return "❌ 导入文本不能为空"

        title = params.get("title", "工具导入")
        agent_id = params.get("agent_id")

        # 直接通过后端 API 创建知识库文档
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "title": title,
                    "content": text,
                    "source": "tool_ingest",
                }
                if agent_id is not None:
                    payload["agent_id"] = agent_id

                resp = await client.post(
                    f"{self.rag.backend_url}/api/knowledge/docs",
                    json=payload,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    doc_id = data.get("data", {}).get("id", "unknown")
                    return f"✅ 已导入文档「{title}」(ID: {doc_id})"
                else:
                    return f"❌ 导入失败: 后端返回 {resp.status_code}"

        except httpx.RequestError as e:
            return f"❌ 导入失败: 后端不可用 - {e}"
        except Exception as e:
            return f"❌ 导入失败: {e}"
