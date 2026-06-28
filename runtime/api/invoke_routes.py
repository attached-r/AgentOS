"""
Agent 调用端点 —— V1 核心闭环 + V2 ReAct Agent 增强。

完整调用链：
  Browser → SpringBoot API → POST /runtime/agents/{id}/invoke → LLM API → 返回

V2 新增：
  - 请求体增加 tools 字段（OpenAI function calling 格式）
  - 有 tools → 使用 ReActAgent 多轮推理循环
  - 无 tools → 保持 V1 行为（直接 LLM 调用）
  - 记忆注入：检索相关记忆拼入 system prompt（V2 修复）
  - 返回工具调用步骤供前端展示（V2 修复）

与其他层的协作：
  1. 从 agent_registry 获取 Agent 配置
  2. 从 MemoryManager 检索相关记忆拼入 system prompt
  3. 用 LLMClient 构造 LLM 客户端
  4. 有 tools → ReActAgent（内部多轮调用，工具执行）
  5. 无 tools → 直接 LLM 调用（与 V1 一致）
  6. 返回结构化结果（content + usage + steps）

错误处理：
  - Agent 不存在 → 404
  - LLM 调用失败 → 502（上游不可用）
  - 请求参数异常 → 400
  - 其他内部错误 → 500
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.registry import agent_registry
from agents.react_agent import ReActAgent
from config import get_config
from context.builder import ContextBuilder, ContextConfig
from core.llm import LLMClient
from tools.registry import tool_registry

router = APIRouter()


# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------

class InvokeRequest(BaseModel):
    """
    调用请求体 —— 与后端 AgentRuntimeClient.InvokeRequest 对应。

    后端使用 camelCase（conversationId），通过 alias 兼容。
    V2 新增 tools 字段：Agent 绑定的 MCP 工具 schema 列表（由后端下发）。
    """
    conversation_id: int = Field(default=0, alias="conversationId")
    messages: list[dict] = Field(default=[])
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    base_url: Optional[str] = Field(default=None, alias="baseUrl")
    tools: Optional[list[dict]] = Field(default=None)  # V2 新增：工具 schema 列表

    model_config = {"populate_by_name": True}


class UsageInfo(BaseModel):
    """Token 用量信息 —— 字段名与后端 AgentRuntimeClient.Usage 对应。"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ToolCallStep(BaseModel):
    """工具调用单步信息 —— 用于前端展示 Thought → Action → Observation 时间线。"""
    step: int = 0
    action: str = ""
    input: str = ""
    output: str = ""


class InvokeResponse(BaseModel):
    """调用响应体 —— 与后端 AgentRuntimeClient.InvokeResponse 对应。"""
    content: str = ""
    usage: UsageInfo = Field(default_factory=UsageInfo)
    steps: List[ToolCallStep] = Field(default_factory=list)  # V2 修复：工具调用步骤


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/{agent_id}/invoke", response_model=InvokeResponse)
async def invoke_agent(agent_id: int, req: InvokeRequest):
    """
    调用指定 Agent 处理消息。

    V2 行为：
      - 如果 req.tools 不为空 → 使用 ReActAgent 多轮推理循环
      - 如果 req.tools 为空   → 保持 V1 行为（直接 LLM 调用）
      - 自动检索相关记忆注入 system prompt

    Args:
        agent_id: Agent ID（与后端 agent 表主键一致）
        req:      请求体（conversation_id + 消息列表 + 可选工具 schema）

    Returns:
        InvokeResponse: { content, usage, steps }

    Raises:
        404: Agent 不存在
        400: 消息列表为空
        502: LLM API 调用失败
    """
    # 1) 从注册表获取 Agent 配置
    config = agent_registry.get_dict(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} 不存在")

    # 2) 参数校验：至少需要一条消息
    if not req.messages:
        raise HTTPException(status_code=400, detail="消息列表不能为空")

    # 3) 如果请求中带了用户自有的 API Key / Base URL，覆盖到 config 中
    if req.api_key:
        config["api_key"] = req.api_key
    if req.base_url:
        config["base_url"] = req.base_url

    # 4) 构造 ContextBuilder（V2 重构：替代手动字符串拼接）
    # ── 使用 ContextBuilder 统一管理记忆 + RAG 注入 ──────────────
    # V2 重构：从手动字符串拼接改为 GSSC（Gather → Structure）模式。
    # 好处：
    #   - 统一入口：记忆/RAG 收集逻辑集中到 ContextBuilder
    #   - 结构化输出：带标签的模板，LLM 能区分信息来源
    #   - V1/V2 共用：两套路径都使用同一份 packets
    base_system_prompt = config.get("system_prompt") or ""
    context_builder = None
    context_packets = None

    # 提取最后一条用户消息用于检索（在 try 外部，确保下游可用）
    last_user_msg = ""
    for msg in reversed(req.messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    try:
        from memory.manager import MemoryManager
        from rag.pipeline import RAGPipeline

        mm = MemoryManager()
        rp = RAGPipeline(backend_url=get_config().backend_base_url)

        context_builder = ContextBuilder(
            config=ContextConfig(memory_limit=5, rag_top_k=3),
            memory=mm,
            rag=rp,
        )

        if last_user_msg:
            context_packets = await context_builder.gather(
                user_query=last_user_msg,
                agent_id=agent_id,
                system_prompt=base_system_prompt,
            )
    except Exception:
        # ContextBuilder/记忆/RAG 初始化失败不阻断主流程
        pass

    # 5) 构造 LLM 客户端
    llm_client = LLMClient.from_agent_config(config)

    # ── 工具 schema 合并 ─────────────────────────────────────────────
    # V2 修复：内置工具（memory、knowledge_retrieval、calculator、web_search）
    # 注册在全局 ToolRegistry 中，但其 schemas 需要显式传给 LLM 才能被调用。
    # 后端下发的 req.tools 包含 MCP 工具（及已绑定 agent_tool 的内置工具），
    # 此处将未重复的内置工具 schemas 合并进去，确保所有内置工具对 LLM 可见。
    #
    # 合并策略：
    #   - 以 req.tools 为基（后端下发的工具，含 agent 绑定的 MCP 工具）
    #   - 追加 ToolRegistry 中的内置工具 schemas（避免 function name 重复）
    builtin_schemas = tool_registry.get_builtin_schemas()
    existing_tool_names: set = set()
    if req.tools:
        for s in req.tools:
            name = s.get("function", {}).get("name", "")
            if name:
                existing_tool_names.add(name)

    merged_tools: List[Dict[str, Any]] = list(req.tools) if req.tools else []
    for schema in builtin_schemas:
        name = schema.get("function", {}).get("name", "")
        if name and name not in existing_tool_names:
            merged_tools.append(schema)
            existing_tool_names.add(name)

    # 工具调用步骤收集器 —— 供 ReActAgent 回传步骤
    tool_steps: List[Dict[str, Any]] = []

    try:
        if merged_tools:
            # ── V2 路径：有工具 → 使用 ReActAgent（含 ContextBuilder）──
            agent = ReActAgent(
                name=config.get("name", f"agent-{agent_id}"),
                llm_client=llm_client,
                system_prompt=base_system_prompt,       # 基础 system prompt（不含记忆/RAG）
                tool_registry=tool_registry,
                max_steps=get_config().react_max_steps,
                tool_steps_collector=tool_steps,
                context_builder=context_builder,         # V2 新增：上下文构建器
            )
            result = await agent.run(
                input_text="",
                messages=req.messages,
                tools=merged_tools,
                context_packets=context_packets,         # V2 新增：预收集的上下文包
                user_query=last_user_msg,                # V2 新增：当前用户问题
            )
        else:
            # ── V1 兼容路径：无工具 → 直接 LLM 调用 ───────────────
            # 使用 ContextBuilder 结构化 system prompt（如有）
            if context_builder and context_packets:
                system_prompt = context_builder.structure(context_packets)
            else:
                system_prompt = base_system_prompt
            result = await llm_client.invoke(
                messages=req.messages,
                system_prompt=system_prompt,
            )

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内部错误: {e}")

    # 5) 返回结构化结果（含工具调用步骤）
    usage = result.get("usage", {})
    return InvokeResponse(
        content=result["content"],
        usage=UsageInfo(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        ),
        steps=[ToolCallStep(**s) for s in tool_steps] if tool_steps else [],
    )
