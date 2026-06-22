"""
Tool 基类 —— 所有工具（内置 + MCP）的抽象接口。

定义了工具的基本生命周期：
  - 名称 / 描述
  - 异步执行（run）
  - 转换为 OpenAI function calling schema（to_openai_schema）

FunctionTool 工具函数封装器：
  将普通 Python 函数快速包装为标准 Tool，
  自动处理参数映射。
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

import inspect


# ---------------------------------------------------------------------------
# Tool 抽象基类
# ---------------------------------------------------------------------------

class Tool(ABC):
    """
    工具基类 — 所有内置工具和 MCP 工具的抽象接口。

    子类必须实现：
      - run()：异步执行工具，返回结果文本
      - to_openai_schema()：返回 OpenAI function calling 格式的 schema
    """

    def __init__(self, name: str, description: str):
        """
        Args:
            name:        工具名称（唯一标识，LLM 通过此名称调用）
            description: 工具描述（LLM 据此判断何时使用该工具）
        """
        self.name = name
        self.description = description

    @abstractmethod
    async def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行工具（异步）。

        Args:
            parameters: 工具参数字典（由 LLM 生成，对应 schema 中的 properties）

        Returns:
            工具执行结果的文本表示
        """
        ...

    @abstractmethod
    def to_openai_schema(self) -> Dict[str, Any]:
        """
        转换为 OpenAI function calling schema。

        Returns:
            格式如 {
                "type": "function",
                "function": {
                    "name": "tool_name",
                    "description": "工具描述",
                    "parameters": {...}
                }
            }
        """
        ...

    def __str__(self) -> str:
        return f"Tool(name={self.name})"


# ---------------------------------------------------------------------------
# FunctionTool —— 将普通 Python 函数包装为 Tool
# ---------------------------------------------------------------------------

class FunctionTool(Tool):
    """
    工具函数封装器。

    将已有的 Python 函数快速包装为标准 Tool 供 Agent 调用。
    适用于将第三方库的函数或已有工具函数注册到 ToolRegistry。

    用法：
        def my_search(query: str) -> str:
            return f"搜索 {query} 的结果..."

        tool = FunctionTool(
            name="search",
            description="搜索工具",
            func=my_search,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        )
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            name:        工具名称
            description: 工具描述
            func:        要包装的函数（可为同步或异步）
            parameters:  OpenAI function calling 格式的参数字典。
                         若不提供，则通过 inspect 自动推断函数签名。
        """
        super().__init__(name, description)
        self._func = func
        self._parameters = parameters or self._infer_parameters()

    async def run(self, parameters: Dict[str, Any]) -> str:
        """执行包装的函数，自动处理同步/异步。"""
        # 提取实际参数（兼容 input 字段映射）
        kwargs = {}
        for key, value in parameters.items():
            kwargs[key] = value
        if not kwargs and "input" in parameters:
            kwargs["input"] = parameters["input"]

        if inspect.iscoroutinefunction(self._func):
            result = await self._func(**kwargs)
        else:
            result = self._func(**kwargs)

        return str(result)

    def to_openai_schema(self) -> Dict[str, Any]:
        """返回 OpenAI function calling 格式的 schema。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._parameters,
            },
        }

    def _infer_parameters(self) -> Dict[str, Any]:
        """
        通过函数签名自动推断参数 schema。

        注意：此方法只能推断参数名称和类型，
        无法生成描述信息。建议显式提供 parameters。
        """
        sig = inspect.signature(self._func)
        properties = {}
        required = []

        for name, param in sig.parameters.items():
            if name == "self":
                continue
            # 推断类型
            if param.annotation is inspect.Parameter.empty:
                param_type = "string"
            elif param.annotation is str:
                param_type = "string"
            elif param.annotation is int or param.annotation is float:
                param_type = "number"
            elif param.annotation is bool:
                param_type = "boolean"
            elif param.annotation is list:
                param_type = "array"
            else:
                param_type = "string"

            properties[name] = {
                "type": param_type,
                "description": f"参数 {name}（自动推断）",
            }

            # 判断是否为必填
            if param.default is inspect.Parameter.empty:
                required.append(name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
