"""
ContextBuilder —— 上下文构建器（仿照 hello_agents GSSC 模式）。

GSSC 流水线（简化版，V2 去掉了 Select / Compress 阶段）：
  1. Gather（收集）    — 从 system_prompt、记忆、RAG 汇集候选信息
  2. Structure（结构化）— 按模板组织为 LLM 友好的格式

核心改进（相对于原来在 invoke_routes.py 中直接做字符串拼接）：
  - 统一入口：不再散落在各个调用点
  - 结构化输出：带标签的模板，LLM 能区分信息来源
  - 可扩展：后续可加 Select（评分/裁剪）和 Compress（压缩）阶段
  - 可测试：独立模块，可单测

用法：
    builder = ContextBuilder(memory=memory_manager, rag=rag_pipeline)
    packets = await builder.gather(
        user_query="如何优化内存?",
        agent_id=1,
        system_prompt="你是 AgentOS 助手...",
    )
    # → 输出结构化 system prompt
    system_prompt = builder.structure(packets)
    # → 或输出完整消息列表
    messages = builder.build_messages(packets, user_query="如何优化内存?")
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# ContextPacket — 候选信息包
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ContextPacket:
    """候选信息包 —— GSSC 流水线中流动的基本数据单元。

    每条 ContextPacket 代表一条候选信息，包含内容、类型标签
    和相关性分数。metadata 中的 type 字段区分信息来源。

    Attributes:
        content:         信息正文
        type:            信息来源类型: system / memory / rag / custom
        relevance_score: 相关性分数 [0.0, 1.0]
        metadata:        附加元数据
    """
    content: str
    type: str = "custom"
    relevance_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# ContextConfig — 上下文构建配置
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ContextConfig:
    """上下文构建配置。

    Attributes:
        memory_limit:     单次记忆检索最大条数
        rag_top_k:        单次 RAG 检索最大条数
        memory_min_importance: 记忆最低重要性阈值，低于此值跳过
    """
    memory_limit: int = 5
    rag_top_k: int = 3
    memory_min_importance: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# ContextBuilder — GSSC 实现（V2 简化版：Gather → Structure）
# ═══════════════════════════════════════════════════════════════════════════════

class ContextBuilder:
    """上下文构建器。

    仿照 hello_agents 的 GSSC 模式，将分散信息汇集为结构化上下文。
    V2 简化版只实现 Gather → Structure 两阶段。

    与 hello_agents 的差异：
      - 没有 Select 阶段（V2 不做评分/裁剪）
      - 没有 Compress 阶段（V2 不做超限压缩）
      - 没有对话历史收集（由上层调用方传入）
      - 接口适配现有 AgentOS 体系

    Args:
        config: 构建配置，不传则使用默认值
        memory: MemoryManager 实例，提供 search() 接口
        rag:    RAGPipeline 实例，提供 retrieve() 接口
    """

    def __init__(
        self,
        config: Optional[ContextConfig] = None,
        memory: Optional[Any] = None,
        rag: Optional[Any] = None,
    ):
        self.config = config or ContextConfig()
        self.memory = memory
        self.rag = rag
        self._logger = logging.getLogger("AgentOS.context.ContextBuilder")

    # ═══════════════════════════════════════════════════════════════════════════
    # Gather（收集）
    # ═══════════════════════════════════════════════════════════════════════════

    async def gather(
        self,
        user_query: str,
        agent_id: int = 0,
        system_prompt: Optional[str] = None,
        custom_packets: Optional[List[ContextPacket]] = None,
    ) -> List[ContextPacket]:
        """Gather 阶段：从多个信息源汇集候选 ContextPacket。

        汇集来源：
          1. 系统指令 → type="system"，最高优先级
          2. 记忆检索 → type="memory"，从 MemoryManager.search() 获取
          3. RAG 检索 → type="rag"，从 RAGPipeline.retrieve() 获取
          4. 自定义包 → 原样加入

        每个外部来源都有 try-except 容错，单源失败不影响其他源。

        Args:
            user_query:    用户当前问题（用于检索记忆和 RAG）
            agent_id:      Agent ID（用于限定搜索范围）
            system_prompt: 系统指令文本
            custom_packets: 调用方自行构造的信息包列表

        Returns:
            候选信息包列表
        """
        packets: List[ContextPacket] = []

        # ── 1. 系统指令 ──────────────────────────────────────────────
        if system_prompt:
            packets.append(ContextPacket(
                content=system_prompt,
                type="system",
                relevance_score=1.0,
                metadata={"priority": "high"},
            ))

        # ── 2. 记忆检索 ──────────────────────────────────────────────
        if self.memory and user_query:
            try:
                items = await self.memory.search(
                    query=user_query,
                    limit=self.config.memory_limit,
                    agent_id=agent_id,
                )
                for item in items:
                    # 跳过重要性低于阈值的记忆
                    if item.importance < self.config.memory_min_importance:
                        continue

                    packets.append(ContextPacket(
                        content=item.content,
                        type="memory",
                        relevance_score=item.importance,
                        metadata={
                            "memory_type": item.memory_type,
                            "memory_id": item.id,
                            "importance": item.importance,
                        },
                    ))
            except Exception as e:
                self._logger.warning("Gather: 记忆检索失败 —— %s", e)

        # ── 3. RAG 检索 ──────────────────────────────────────────────
        if self.rag and user_query:
            try:
                chunks = await self.rag.retrieve(
                    query=user_query,
                    agent_id=agent_id,
                    top_k=self.config.rag_top_k,
                )
                if chunks:
                    context = self.rag.build_context(chunks)
                    packets.append(ContextPacket(
                        content=context,
                        type="rag",
                        relevance_score=0.8,
                        metadata={"source": "knowledge_base"},
                    ))
            except Exception as e:
                self._logger.warning("Gather: RAG 检索失败 —— %s", e)

        # ── 4. 自定义信息包 ──────────────────────────────────────────
        if custom_packets:
            packets.extend(custom_packets)

        self._logger.info(
            "Gather: 汇集约 %d 个信息包",
            len(packets),
        )
        return packets

    # ═══════════════════════════════════════════════════════════════════════════
    # Structure（结构化）
    # ═══════════════════════════════════════════════════════════════════════════

    def structure(self, packets: List[ContextPacket]) -> str:
        """将选中的信息包组织为带标签的结构化 system prompt。

        输出格式：
          [系统指令]
          ...

          [相关记忆]
          ...

          [知识库参考]
          ...

        按类型分组输出，LLM 能清晰区分信息来源。

        Args:
            packets: ContextPacket 列表

        Returns:
            结构化的 system prompt 字符串
        """
        sections: List[str] = []

        # 按类型分组
        system_blocks: List[str] = []
        memory_blocks: List[str] = []
        rag_blocks: List[str] = []
        other_blocks: List[str] = []

        for p in packets:
            if p.type == "system":
                system_blocks.append(p.content)
            elif p.type == "memory":
                memory_blocks.append(p.content)
            elif p.type == "rag":
                rag_blocks.append(p.content)
            else:
                other_blocks.append(p.content)

        # [系统指令]
        if system_blocks:
            sections.append("【角色与规则】\n" + "\n".join(system_blocks))

        # [相关记忆]
        if memory_blocks:
            lines = ["【相关记忆】"]
            for i, m in enumerate(memory_blocks, 1):
                lines.append(f"  [{i}] {m}")
            sections.append("\n".join(lines))

        # [知识库参考]
        if rag_blocks:
            sections.append("【知识库参考】\n" + "\n".join(rag_blocks))

        # [其他]
        if other_blocks:
            sections.append("【辅助信息】\n" + "\n".join(other_blocks))

        return "\n\n".join(sections)

    # ═══════════════════════════════════════════════════════════════════════════
    # 便捷方法：构建消息列表
    # ═══════════════════════════════════════════════════════════════════════════

    def build_messages(
        self,
        packets: Optional[List[ContextPacket]] = None,
        user_query: str = "",
        existing_messages: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """构建完整的 OpenAI 兼容消息列表。

        消息顺序：
          1. system: 结构化后的 system prompt（含记忆/RAG 上下文）
          2. 已有对话历史（过滤掉原有的 system 消息避免重复）
          3. user: 当前用户输入

        Args:
            packets:           ContextPacket 列表
            user_query:        用户当前输入
            existing_messages: 已有的消息列表（来自前端或历史）

        Returns:
            [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, ...]
        """
        messages: List[Dict[str, str]] = []

        # 1. 系统指令（结构化上下文）
        if packets:
            system_content = self.structure(packets)
            if system_content:
                messages.append({"role": "system", "content": system_content})

        # 2. 已有对话历史
        if existing_messages:
            for msg in existing_messages:
                role = msg.get("role", "")
                # 过滤掉原有 system 消息（已被结构化的 system prompt 替代）
                if role != "system":
                    messages.append(msg)

        # 3. 当前用户输入
        if user_query:
            # 检查是否已有 user 消息（避免重复）
            has_user = any(
                m.get("role") == "user" and m.get("content") == user_query
                for m in messages
            )
            if not has_user:
                messages.append({"role": "user", "content": user_query})

        return messages
