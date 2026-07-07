"""MCP SSE 测试服务器 — 启动后供 AgentOS 同步测试用。
启动: uv run python runtime/scripts/test_mcp_server.py
服务在 http://localhost:8080/mcp
"""
import uvicorn
from fastmcp import FastMCP

mcp = FastMCP("test-server")


@mcp.tool()
def greet(name: str) -> str:
    """向用户打招呼"""
    return f"你好, {name}!"


@mcp.tool()
def add(a: float, b: float) -> float:
    """两个数相加"""
    return a + b


if __name__ == "__main__":
    mcp.run(transport="sse", port=8080, host="0.0.0.0", path="/mcp")
