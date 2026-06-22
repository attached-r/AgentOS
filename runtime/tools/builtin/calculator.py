"""
CalculatorTool —— 数学计算工具（内置工具）。

通过 Python eval 安全执行简单算术表达式。
支持 +、-、*、/、幂运算、括号、浮点数。
"""
import re
from typing import Any, Dict

from tools.base import Tool


# ---------------------------------------------------------------------------
# CalculatorTool
# ---------------------------------------------------------------------------

class CalculatorTool(Tool):
    """
    数学计算工具。

    使用 Python eval 执行算术表达式，包含严格的安全检查。
    只允许数字、运算符、括号、空格、小数点和百分号。
    """

    # 安全字符白名单：数字、运算符、括号、空格、小数点、逗号（千分位）、百分号
    SAFE_PATTERN = r'^[\d\s\+\-\*\/\(\)\.\,%]+$'

    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算，支持加(+)、减(-)、乘(*)、除(/)、幂运算(**)、括号。"
                        "输入应为纯数学表达式，如 \"15 * 8 + 32\"",
        )

    async def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行数学计算。

        从 parameters 中获取表达式，支持以下键（按优先级）：
          - expression
          - input
          - 直接传入 {"expression": "15 * 8 + 32"}

        Args:
            parameters: 工具参数字典，包含 expression 字段

        Returns:
            计算结果的文本表示，如 "15 * 8 + 32 = 152"
        """
        # 提取表达式（兼容多种参数名）
        expression = (parameters.get("expression")
                      or parameters.get("input")
                      or "")

        if not expression.strip():
            return "错误：表达式不能为空"

        # 安全检查：只允许数字、运算符、括号、空格
        if not re.match(self.SAFE_PATTERN, expression):
            return f"错误：表达式包含不允许的字符: {expression}"

        try:
            # 安全执行：禁止内置函数和变量
            result = eval(expression, {"__builtins__": {}}, {})
            return f"{expression} = {result}"
        except ZeroDivisionError:
            return f"错误：除数不能为零"
        except Exception as e:
            return f"计算错误: {e}"

    def to_openai_schema(self) -> Dict[str, Any]:
        """返回 OpenAI function calling 格式的 schema。"""
        return {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 \"15 * 8 + 32\"。"
                                           "支持运算符：+ - * / ** ( )",
                        },
                    },
                    "required": ["expression"],
                },
            },
        }
