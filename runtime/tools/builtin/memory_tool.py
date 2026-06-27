"""
MemoryTool —— 记忆管理工具（内置工具）。

将 MemoryManager 封装为 Tool，供 Agent 在推理循环中主动调用。
Agent 可通过此工具保存观察结果、检索历史记忆、管理记忆生命周期。

与被动记忆注入（invoke_routes.py 中的预先检索）互为补充：
  - 被动注入：每次调用前自动检索相关记忆拼入 system prompt（无需 Agent 干预）
  - 主动工具：Agent 在推理过程中按需调用，可保存新信息或深度检索

支持的操作:
  add          添加记忆
  search       检索记忆
  summary      记忆统计摘要
  consolidate  执行记忆整合（工作记忆 → 情景记忆）
  clear        清空工作记忆

V2 简化说明：
  - forget 操作暂不实现（MemoryManager 尚无 forget 方法）
  - update/remove 仅支持 working 类型记忆（episodic 需通过后端 API）
  - 记忆检索基于关键词 ILIKE 匹配（V3 升级 Qdrant 向量检索）
"""
from typing import Any, Dict

from tools.base import Tool
from memory.manager import MemoryManager


class MemoryTool(Tool):
    """
    记忆管理工具。

    Agent 可通过此工具主动操作记忆系统：
      - 保存重要信息到工作记忆或情景记忆
      - 按关键词检索相关历史记忆
      - 查看记忆统计和整合记忆
      - 清空工作记忆

    用法（由 ToolRegistry 自动注册，Agent 通过 function calling 调用）：
      { "action": "search", "query": "用户偏好", "limit": 5 }
      { "action": "add", "content": "用户喜欢简洁的回答", "memory_type": "episodic" }
    """

    def __init__(self, memory: MemoryManager):
        """
        Args:
            memory: MemoryManager 实例（全局共享，确保工作记忆跨轮次可用）
        """
        super().__init__(
            name="memory",
            description=(
                "记忆管理工具。用于存储和检索Agent的记忆信息，"
                "支持工作记忆（当前会话）和情景记忆（跨会话持久化）两种类型。"
            ),
        )
        self.memory = memory

    async def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行记忆操作。

        根据 action 参数分发到对应的处理方法。

        Args:
            parameters: 工具参数字典，必须包含 "action" 字段

        Returns:
            操作结果文本
        """
        action = parameters.get("action", "search")
        handler = getattr(self, f"_{action}", None)
        if handler is None:
            return (
                f"未知操作: {action}，支持: "
                f"add/search/summary/consolidate/clear"
            )
        return await handler(**parameters)

    def to_openai_schema(self) -> Dict[str, Any]:
        """返回 OpenAI function calling 格式的 schema。"""
        return {
            "type": "function",
            "function": {
                "name": "memory",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "操作类型",
                            "enum": ["add", "search", "summary", "consolidate", "clear"],
                        },
                        "content": {
                            "type": "string",
                            "description": "记忆内容（add 操作需要）",
                        },
                        "query": {
                            "type": "string",
                            "description": "检索关键词（search 操作需要）",
                        },
                        "memory_type": {
                            "type": "string",
                            "description": "记忆类型: working（当前会话）/ episodic（跨会话持久）",
                            "enum": ["working", "episodic"],
                        },
                        "importance": {
                            "type": "number",
                            "description": "重要性 0.0 ~ 1.0（add 操作可选，默认 0.5）",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "检索返回条数上限（search 操作可选，默认 5）",
                        },
                        "agent_id": {
                            "type": "integer",
                            "description": "Agent ID（add/search 操作筛选所属 Agent）",
                        },
                        "user_id": {
                            "type": "integer",
                            "description": "用户 ID（add 操作用于记录所属用户）",
                        },
                    },
                    "required": ["action"],
                },
            },
        }

    # ── 操作实现 ──────────────────────────────────────────────────

    async def _add(self, **params) -> str:
        """
        添加一条记忆。

        根据 memory_type 决定存储层级：
          - working:  存入内存，当前会话有效，TTL 过期后自动淘汰
          - episodic: 通过后端 API 持久化到 PostgreSQL，跨会话可用

        Args:
            params: content（必填）, memory_type, importance, agent_id, user_id

        Returns:
            操作结果文本（含记忆 ID）
        """
        content = params.get("content", "")
        if not content:
            return "❌ 记忆内容不能为空"

        memory_type = params.get("memory_type", "working")
        importance = float(params.get("importance", 0.5))
        agent_id = int(params.get("agent_id", 0))
        user_id = int(params.get("user_id", 0))

        try:
            mid = await self.memory.save(
                content=content,
                memory_type=memory_type,
                importance=importance,
                agent_id=agent_id,
                user_id=user_id,
            )
            return f"✅ 已添加 {memory_type} 记忆 (ID: {mid})"
        except NotImplementedError:
            return f"❌ {memory_type} 记忆类型尚未实现"
        except Exception as e:
            return f"❌ 添加失败: {e}"

    async def _search(self, **params) -> str:
        """
        检索记忆。

        跨工作记忆和情景记忆搜索，按重要性降序返回。
        V2 使用关键词 ILIKE 匹配，V3 升级 Qdrant 向量检索。

        Args:
            params: query（必填）, memory_type（可选过滤）, limit, agent_id

        Returns:
            格式化后的检索结果文本
        """
        query = params.get("query", "")
        if not query:
            return "❌ 检索内容不能为空"

        memory_type = params.get("memory_type")
        limit = int(params.get("limit", 5))
        agent_id = int(params.get("agent_id", 0))

        try:
            results = await self.memory.search(
                query, memory_type=memory_type, limit=limit, agent_id=agent_id
            )
            if not results:
                return "💡 未找到相关记忆"

            lines = [f"🔍 找到 {len(results)} 条相关记忆:\n"]
            for i, item in enumerate(results):
                # 取内容前 200 字符展示
                content_preview = item.content[:200].replace("\n", " ")
                lines.append(
                    f"  [{i+1}] [{item.memory_type}] {content_preview}\n"
                )
            return "\n".join(lines)
        except NotImplementedError:
            return f"❌ {memory_type or '全部'} 记忆类型尚未实现"
        except Exception as e:
            return f"❌ 检索失败: {e}"

    async def _summary(self, **params) -> str:
        """
        返回记忆系统的统计摘要。

        Returns:
            格式化的统计信息文本
        """
        stats = await self.memory.stats()
        lines = ["📊 记忆统计:\n"]
        lines.append(f"  - 工作记忆: {stats.get('working_count', 0)} 条\n")
        lines.append(f"  - 情景记忆: {stats.get('episodic_count', 0)} 条\n")
        return "".join(lines)

    async def _consolidate(self, **params) -> str:
        """
        执行记忆整合。

        遍历工作记忆，将重要性高于阈值的项提升为情景记忆（持久化）。
        模拟人脑睡眠时的记忆巩固过程。

        Returns:
            整合结果文本
        """
        count = await self.memory.consolidate()
        return f"✅ 已整合 {count} 条记忆到情景记忆"

    async def _clear(self, **params) -> str:
        """
        清空工作记忆。

        Returns:
            操作结果文本
        """
        await self.memory.clear_working()
        return "✅ 已清空工作记忆"
