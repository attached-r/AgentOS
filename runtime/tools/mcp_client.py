"""
MCP 客户端封装 —— 连接外部 MCP 服务器并调用工具。

基于 fastmcp 2.x 实现，支持 SSE 和 stdio 两种传输模式。

两种使用模式：
  1. 同步模式（sync）：连接 MCP 服务器 → 拉取工具列表 → 缓存 schema → 断开
     对应 V2 MCP 同步流程，返回工具列表给后端存储。
  2. 调用模式（call）：通过缓存的工具信息调用远程工具
     对应 ReActAgent 执行 MCP 工具的场景，需要保持长连接。

V2 简化方案：
  - MCP 同步时拉取所有工具的 schema 并缓存到内存
  - 工具调用时复用缓存的客户端连接
  - 暂不实现 Resources / Prompts，只聚焦 Tool
"""
from typing import Any, Dict, List, Optional

from tools.base import Tool


# ---------------------------------------------------------------------------
# MCPToolClient
# ---------------------------------------------------------------------------

class MCPToolClient:
    """
    MCP 客户端封装。

    包装 fastmcp.Client，提供工具发现和调用能力。
    每种传输模式（SSE / stdio）对应不同的连接方式。

    用法：
        # 同步工具列表
        client = MCPToolClient(endpoint="http://localhost:8000/mcp", transport="sse")
        await client.connect()
        tools = await client.list_tools()
        # tools = [{"name": "...", "description": "...", "inputSchema": {...}}, ...]

        # 调用工具
        result = await client.call_tool("tool_name", {"param": "value"})
        await client.disconnect()
    """

    def __init__(
        self,
        endpoint: str,
        transport: str = "sse",
        timeout: int = 30,
    ):
        """
        Args:
            endpoint:   MCP 服务器地址
                       SSE 模式: HTTP URL，如 "http://localhost:8000/mcp"
                       stdio 模式: 命令字符串或脚本路径
            transport:  传输协议， "sse" 或 "stdio"
            timeout:    连接超时秒数
        """
        self.endpoint = endpoint
        self.transport = transport
        self.timeout = timeout

        # fastmcp.Client 实例（连接后创建）
        self._client: Optional[Any] = None
        # 缓存的工具列表 [{name, description, inputSchema, openai_schema}]
        self._tools: List[Dict[str, Any]] = []

    # ── 连接生命周期 ──────────────────────────────────────────────

    async def connect(self) -> None:
        """
        连接 MCP 服务器。

        根据 transport 类型选择合适的传输方式：
          - "sse":   通过 HTTP/SSE 连接远程 MCP 服务器
          - "stdio": 通过子进程管道连接本地 MCP 服务器

        Raises:
            RuntimeError: 连接失败
        """
        try:
            import fastmcp

            if self.transport == "sse":
                # SSE 模式：通过 URL 连接远程 MCP 服务器
                from fastmcp.client.transports.sse import SSETransport

                transport = SSETransport(
                    url=self.endpoint,
                    timeout=self.timeout,
                )
            elif self.transport == "stdio":
                # stdio 模式：通过命令启动本地 MCP 服务器进程
                from fastmcp.client.transports.stdio import StdioTransport

                # endpoint 为命令字符串，按空格分割
                parts = self.endpoint.split()
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []

                transport = StdioTransport(
                    command=command,
                    args=args,
                )
            else:
                raise ValueError(f"不支持的传输协议: {self.transport}（支持: sse, stdio）")

            self._client = fastmcp.Client(transport)
            await self._client.__aenter__()

        except ImportError as e:
            raise RuntimeError(f"fastmcp 库未安装: {e}") from e
        except Exception as e:
            raise RuntimeError(f"MCP 连接失败 ({self.transport}): {e}") from e

    async def disconnect(self) -> None:
        """断开 MCP 连接，释放资源。"""
        if self._client is not None:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:
                pass  # 断开失败不影响主流程
            finally:
                self._client = None
                self._tools = []

    # ── 工具发现与调用 ────────────────────────────────────────────

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        拉取 MCP 服务器的工具列表。

        每个工具包含以下字段：
          - name:        工具名称
          - description: 工具描述
          - inputSchema: 输入参数的 JSON Schema
          - openai_schema: 转换后的 OpenAI function calling schema

        Returns:
            工具字典列表（已缓存到 self._tools）
        """
        self._require_connected()

        raw_tools = await self._client.list_tools()

        self._tools = []
        for t in raw_tools:
            # 获取工具属性（兼容不同版本的 fastmcp）
            tool_name = getattr(t, "name", "")
            tool_desc = getattr(t, "description", "")
            tool_schema = getattr(t, "inputSchema", {})

            # 转换为 OpenAI function calling 格式
            openai_schema = self._to_openai_schema(tool_name, tool_desc, tool_schema)

            self._tools.append({
                "name": tool_name,
                "description": tool_desc,
                "inputSchema": tool_schema,
                "openai_schema": openai_schema,
            })

        return self._tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        调用 MCP 服务器上的工具。

        Args:
            tool_name:  工具名称
            arguments:  工具参数

        Returns:
            工具执行结果的文本表示

        Raises:
            RuntimeError: 调用失败或未连接
        """
        self._require_connected()

        try:
            result = await self._client.call_tool(tool_name, arguments or {})

            # 提取结果文本（兼容不同版本的 fastmcp 返回格式）
            content = getattr(result, "content", [])
            if content and isinstance(content, list):
                texts = []
                for item in content:
                    text = getattr(item, "text", str(item))
                    texts.append(text)
                return "\n".join(texts)

            # 兜底：直接转为字符串
            return str(result)

        except Exception as e:
            return f"MCP 工具调用失败 [{tool_name}]: {e}"

    # ── 查询方法 ──────────────────────────────────────────────────

    def has_tool(self, name: str) -> bool:
        """检查是否包含指定名称的工具。"""
        return any(t["name"] == name for t in self._tools)

    def list_tool_names(self) -> List[str]:
        """返回所有缓存的工具名称列表。"""
        return [t["name"] for t in self._tools]

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        """
        返回缓存的工具 OpenAI function calling schema 列表。

        Returns:
            OpenAI function calling schema 列表
        """
        schemas = []
        for t in self._tools:
            schema = t.get("openai_schema")
            if schema:
                schemas.append(schema)
        return schemas

    @property
    def connected(self) -> bool:
        """是否已连接到 MCP 服务器。"""
        return self._client is not None

    # ── 内部方法 ──────────────────────────────────────────────────

    def _to_openai_schema(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        将 MCP 工具格式转换为 OpenAI function calling schema。

        MCP inputSchema 已经是 JSON Schema 格式（type: object, properties, required），
        可复用为 OpenAI function 的 parameters。

        Args:
            name:         工具名称
            description:  工具描述
            input_schema: MCP inputSchema（JSON Schema 格式）

        Returns:
            OpenAI function calling 格式的 schema
        """
        # 如果 input_schema 为空，使用默认结构
        if not input_schema:
            input_schema = {
                "type": "object",
                "properties": {},
                "required": [],
            }

        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description or f"MCP tool: {name}",
                "parameters": input_schema,
            },
        }

    def _require_connected(self) -> None:
        """检查连接状态，未连接时抛出 RuntimeError。"""
        if not self.connected:
            raise RuntimeError(
                "MCP 客户端未连接。请先调用 connect()。"
            )
