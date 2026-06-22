# runtime/tools/builtin — 内置工具包
#
# 内置工具不经过 MCP 协议，由 Runtime 本地直接调用 Python 函数。
# 所有内置工具在 Runtime 启动时通过 ToolRegistry.register_builtins() 自动注册。
#
# 内置工具对所有 Agent 默认可用，无需绑定。
