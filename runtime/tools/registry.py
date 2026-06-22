"""
ToolRegistry —— 工具注册中心。

管理 Agent 可用的所有工具，提供注册、执行、schema 导出能力。

工具来源分两类：
  1. 内置工具（builtin）：Runtime 启动时通过 register_builtins() 自动注册，
     所有 Agent 默认可用。不经过 MCP 协议，直调 Python 函数。
  2. MCP 工具（mcp）：通过 MCP 同步流程注册，MCPToolClient 持久化管理。
     Agent 与 MCP 工具的绑定关系由后端管理（agent_tool 表）。

V2 设计要点：
  - ToolRegistry 不维护 agent_tool 绑定关系（后端管理）
  - 只负责"注册 → 执行"的映射
  - 内置工具对所有 Agent 默认可用
  - MCP 工具通过后端下发的 schemas 决定 Agent 可用性
  - 全局单例，跨请求复用 MCP 客户端连接
"""
from typing import Any, Dict, List, Optional

from tools.base import Tool


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """
    工具注册中心。

    提供工具的注册、查找、执行和 schema 导出。
    内置工具和 MCP 工具均通过此注册中心管理。
    """

    def __init__(self):
        # name -> Tool 实例（内置工具，直调 Python 函数）
        self._tools: Dict[str, Tool] = {}
        # endpoint -> MCPToolClient（MCP 远程工具客户端，延迟导入避免循环依赖）
        self._mcp_clients: Dict[str, "MCPToolClient"] = {}

    # ── 注册（内置工具） ──────────────────────────────────────────────

    def register_tool(self, tool: Tool) -> None:
        """
        注册单个内置工具。

        Args:
            tool: Tool 实例
        """
        self._tools[tool.name] = tool

    def register_builtins(self) -> None:
        """
        注册所有内置工具。

        在 Runtime 启动时调用，为所有 Agent 注册默认可用工具。
        当前注册：
          - CalculatorTool：数学计算
          - SearchTool：网页搜索
        """
        from tools.builtin.calculator import CalculatorTool
        from tools.builtin.search import SearchTool

        self.register_tool(CalculatorTool())
        self.register_tool(SearchTool())

    # ── 注册（MCP 工具） ──────────────────────────────────────────────

    def register_mcp_client(self, client: "MCPToolClient") -> None:
        """
        注册 MCP 客户端。

        MCP 同步成功后调用，缓存客户端以便后续工具调用。

        Args:
            client: MCPToolClient 实例
        """
        self._mcp_clients[client.endpoint] = client

    def get_mcp_clients(self) -> Dict[str, "MCPToolClient"]:
        """获取所有已注册的 MCP 客户端。"""
        return dict(self._mcp_clients)

    # ── 执行 ──────────────────────────────────────────────────────────

    async def execute(self, name: str, params: Dict[str, Any]) -> str:
        """
        按名称执行工具。

        查找顺序：内置工具 → MCP 工具

        Args:
            name:   工具名称
            params: 工具参数字典

        Returns:
            工具执行结果文本

        Raises:
            ValueError: 工具未找到时抛出
        """
        # 1) 查找内置工具
        if name in self._tools:
            return await self._tools[name].run(params)

        # 2) 查找 MCP 工具
        for client in self._mcp_clients.values():
            if await client.has_tool(name):
                return await client.call_tool(name, params)

        raise ValueError(f"工具 '{name}' 未在注册表中找到")

    def is_builtin(self, name: str) -> bool:
        """判断是否为内置工具。"""
        return name in self._tools

    # ── Schema 导出 ───────────────────────────────────────────────────

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        """
        返回所有注册工具的 OpenAI function calling schema 列表。

        注意：invoke 端点使用的 tools schemas 来自后端请求体（req.tools），
        而非此方法。此方法主要用于 MCP 同步等场景。

        Returns:
            OpenAI function calling schema 列表
        """
        schemas: List[Dict[str, Any]] = []

        # 内置工具 schema
        for tool in self._tools.values():
            schemas.append(tool.to_openai_schema())

        # MCP 工具 schema
        for client in self._mcp_clients.values():
            schemas.extend(client.get_openai_schemas())

        return schemas

    # ── 查询 ──────────────────────────────────────────────────────────

    def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称。"""
        names = list(self._tools.keys())
        for client in self._mcp_clients.values():
            names.extend(client.list_tool_names())
        return names

    def count(self) -> int:
        """返回已注册的工具总数（含 MCP）。"""
        count = len(self._tools)
        for client in self._mcp_clients.values():
            count += len(client.list_tool_names())
        return count


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------
# 运行时全局唯一的工具注册表实例。
# 在 main.py 启动时调用 register_builtins() 初始化。
tool_registry = ToolRegistry()
