"""
Agent 调用端点 —— V1 核心闭环。

完整调用链：
  Browser → SpringBoot API → POST /runtime/agents/{id}/invoke → LLM API → 返回

与其他层的协作：
  1. 从 agent_registry 获取 Agent 配置
  2. 用 LLMClient 构造 LLM 客户端
  3. 直接调用 LLM（后端已传入完整消息列表，不走 agent 内部历史）
  4. 返回结构化结果（content + usage）

错误处理：
  - Agent 不存在 → 404
  - LLM 调用失败 → 502（上游不可用）
  - 请求参数异常 → 400
  - 其他内部错误 → 500
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.registry import agent_registry
from core.llm import LLMClient

router = APIRouter()


# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------

class InvokeRequest(BaseModel):
    """
    调用请求体 —— 与后端 AgentRuntimeClient.InvokeRequest 对应。

    后端使用 camelCase（conversationId），通过 alias 兼容。
    """
    conversation_id: int = Field(default=0, alias="conversationId")
    messages: list[dict] = Field(default=[])

    model_config = {"populate_by_name": True}


class UsageInfo(BaseModel):
    """Token 用量信息 —— 字段名与后端 AgentRuntimeClient.Usage 对应。"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class InvokeResponse(BaseModel):
    """调用响应体 —— 与后端 AgentRuntimeClient.InvokeResponse 对应。"""
    content: str = ""
    usage: UsageInfo = Field(default_factory=UsageInfo)


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/{agent_id}/invoke", response_model=InvokeResponse)
async def invoke_agent(agent_id: int, req: InvokeRequest):
    """
    调用指定 Agent 处理消息。

    流程：
      1. 从注册表获取 Agent 配置
      2. 构造 LLM 客户端
      3. 后端已在 req.messages 中传入了完整的消息列表
         （含历史消息），所以直接传给 LLMClient
      4. 返回结构化的响应

    Args:
        agent_id: Agent ID（与后端 agent 表主键一致）
        req:      请求体（conversation_id + 消息列表）

    Returns:
        InvokeResponse: { content, usage: { prompt_tokens, completion_tokens, total_tokens } }

    Raises:
        404: Agent 不存在
        400: 消息列表中没有 user 消息
        502: LLM API 调用失败
    """
    # 1) 从注册表获取 Agent 配置
    config = agent_registry.get_dict(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} 不存在")

    # 2) 参数校验：至少需要一条消息
    if not req.messages:
        raise HTTPException(status_code=400, detail="消息列表不能为空")

    # 3) 构造 LLM 客户端，直接调用（后端已传入完整消息列表）
    llm_client = LLMClient.from_agent_config(config)

    try:
        result = await llm_client.invoke(
            messages=req.messages,
            system_prompt=config.get("system_prompt"),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内部错误: {e}")

    # 4) 返回结构化结果
    usage = result.get("usage", {})
    return InvokeResponse(
        content=result["content"],
        usage=UsageInfo(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        ),
    )
