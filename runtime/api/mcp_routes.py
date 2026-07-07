"""
MCP 工具同步端点 —— V2 新增。

后端注册 MCP 服务后，调用此接口让 Runtime 连接 MCP 服务器并拉取工具列表。
返回的工具列表由后端存储到 tool 表，并在 Agent 调用时下发给 Runtime。

同步流程：
  1. 后端 POST /api/mcp-servers 注册 MCP 服务
  2. 后端调用 Runtime: POST /runtime/mcp/sync { endpoint, transport }
  3. Runtime 的 MCPToolClient 连接该 MCP 服务器
  4. 调用 list_tools() 拉取所有工具的 schema
  5. 返回工具列表（JSON 数组）
  6. 后端保存到 tool 表（计算 version_hash 去重）

注意：返回的是 JSON 数组（非包裹对象），
与后端 AgentRuntimeClient.syncTools() 中 ToolSchema[] 的反序列化格式匹配。
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import get_config
from tools.mcp_client import MCPToolClient
from tools.registry import tool_registry

router = APIRouter()


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------

class McpSyncRequest(BaseModel):
    """
    MCP 同步请求体。

    对应后端 McpSyncRequest / AgentRuntimeClient.syncTools 的参数。
    """
    endpoint: str                                              # MCP 服务器地址
    transport: str = "sse"                                     # 传输协议：sse / stdio


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/mcp/sync")
async def sync_mcp_tools(req: McpSyncRequest):
    """
    连接 MCP 服务器，拉取工具列表和 schema。

    流程：
      1. 创建 MCPToolClient 并连接到指定服务器
      2. 调用 list_tools() 获取所有工具
      3. 将 MCP 客户端注册到全局 ToolRegistry（用于后续工具调用）
      4. 返回工具列表给后端

    Returns:
        JSON 数组，每个元素为 { name, description, inputSchema, openai_schema }

    Raises:
        502: MCP 连接或同步失败
    """
    try:
        config = get_config()

        # 创建 MCP 客户端并连接
        client = MCPToolClient(
            endpoint=req.endpoint,
            transport=req.transport,
            timeout=config.mcp_connection_timeout,
            read_timeout=config.mcp_read_timeout,
        )

        await client.connect()

        # 拉取工具列表
        tools = await client.list_tools()

        # 注册到全局 ToolRegistry，以便后续 ReActAgent 工具调用
        tool_registry.register_mcp_client(client)

        # 返回 JSON 数组（后端 AgentRuntimeClient.syncTools 期望 ToolSchema[]）
        return tools

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"MCP 同步失败: {e}")
