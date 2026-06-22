# runtime/tools — 工具系统
#
# 包含：
#   base.py       — Tool 基类 + FunctionTool 封装
#   registry.py   — ToolRegistry（全局单例）
#   mcp_client.py — MCP 客户端封装
#   builtin/      — 内置工具（Calculator、Search 等）
#
# V2 设计原则：
#   - 内置工具由 Runtime 启动时自动注册，所有 Agent 默认可用
#   - MCP 工具通过同步流程注册，与 Agent 绑定关系由后端管理
