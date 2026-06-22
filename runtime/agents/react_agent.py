"""
ReActAgent —— 推理-行动循环 Agent（V2 核心新增）。

流程：LLM(带 tools) → tool_call? → 执行工具 → 追加结果 → 继续调用 LLM → ... → 最终文本

使用 LLM 原生的 function calling 能力（而非文本解析），更可靠。
无工具时退化为简单的 LLM 单次调用（兼容 V1 行为）。

与 SimpleAgent 的关系：
  - SimpleAgent：单次 LLM 调用，直接返回（用于纯对话场景）
  - ReActAgent：多轮循环，每轮可调用工具，直到 LLM 输出纯文本
  - 两者均继承 BaseAgent
"""
import json
from typing import Any, Dict, List, Optional

from core.agent import BaseAgent
from core.llm import LLMClient
from core.message import Message
from tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# ReActAgent
# ---------------------------------------------------------------------------

class ReActAgent(BaseAgent):
    """
    推理-行动循环 Agent。

    使用 LLM 的 function calling 能力进行多轮推理：
      1. 将工具 schema 传递给 LLM
      2. LLM 若判断需要工具 → 返回 tool_calls
      3. 执行工具 → 将结果作为 tool message 追加到对话
      4. 继续调用 LLM → 重复 2-4 直到 LLM 输出纯文本
      5. 达到 max_steps 则强制结束

    无工具时（tools=None），行为退化为简单 LLM 调用。
    """

    def __init__(
        self,
        name: str,
        llm_client: LLMClient,
        system_prompt: Optional[str] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_steps: int = 10,
        tool_steps_collector: Optional[list] = None,  # V2 修复：外部步骤收集器
    ):
        """
        Args:
            name:          Agent 名称
            llm_client:    LLM 客户端
            system_prompt: 系统提示词
            tool_registry: 工具注册表（用于执行工具调用）
            max_steps:     推理-行动循环的最大步数，防止无限循环
            tool_steps_collector: 外部列表引用，每步工具调用信息追加到此列表
        """
        super().__init__(name, llm_client, system_prompt)
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.tool_steps_collector = tool_steps_collector  # V2 修复

    async def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        ReAct 循环执行。

        Args:
            input_text: 用户输入（当 messages 为空时使用）
            **kwargs:
                messages: 现有的完整消息列表（后端传入，含 system + 历史 + 当前消息）
                tools:    OpenAI function calling 格式的工具 schema 列表
                          由后端从 agent_tool 关联表查询并下发的 MCP 工具列表
                          （内置工具的 schema 也由后端一并下发）

        Returns:
            {
                "content": "最终回复文本",
                "usage": {
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int,
                }
            }
        """
        # 获取消息列表和工具列表
        messages = list(kwargs.get("messages", []))
        if not messages:
            messages = self.build_messages(input_text)

        tools: Optional[List[Dict]] = kwargs.get("tools")

        # 累计 token 用量（多轮调用的总和）
        total_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        # ── ReAct 循环 ─────────────────────────────────────────────
        for step in range(1, self.max_steps + 1):
            # 1) 调用 LLM（携带工具 schema）
            result = await self.llm_client.invoke(
                messages=messages,
                system_prompt=None,  # system 已在 messages 中
                tools=tools,
            )

            # 合并 token 用量
            step_usage = result.get("usage", {})
            for key in total_usage:
                total_usage[key] += step_usage.get(key, 0)

            # 提取 LLM 回复
            content = result.get("content", "")
            tool_calls = result.get("tool_calls")

            if tool_calls:
                # 2) 有工具调用 → 执行 → 追加到消息列表 → 继续循环
                # 构建 assistant 消息（含 tool_calls）
                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": content or None,  # tool_call 时 content 可为空
                }

                # 序列化 tool_calls 为可序列化格式
                serialized_calls = []
                for tc in tool_calls:
                    call_id = getattr(tc, "id", f"call_{step}_{len(serialized_calls)}")
                    func_name = getattr(tc.function, "name", "")
                    func_args = getattr(tc.function, "arguments", "{}")

                    serialized_calls.append({
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": func_name,
                            "arguments": func_args,
                        },
                    })

                assistant_msg["tool_calls"] = serialized_calls
                messages.append(assistant_msg)

                # 逐个执行工具
                for tc in tool_calls:
                    call_id = getattr(tc, "id", "")
                    func_name = getattr(tc.function, "name", "")
                    func_args_str = getattr(tc.function, "arguments", "{}")

                    # 解析参数
                    try:
                        args = json.loads(func_args_str)
                    except json.JSONDecodeError:
                        args = {}

                    # 执行工具
                    tool_result = await self._execute_tool(func_name, args)

                    # V2 修复：记录工具调用步骤供前端展示
                    if self.tool_steps_collector is not None:
                        self.tool_steps_collector.append({
                            "step": step,
                            "action": func_name,
                            "input": func_args_str,
                            "output": tool_result[:500],  # 截断过长输出
                        })

                    # 将工具结果追加为 tool message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": tool_result,
                    })

                # 继续下一轮循环
                continue

            else:
                # 3) 无工具调用 → LLM 输出最终文本 → 返回
                # 记录到历史
                self.add_message(Message(role="user", content=input_text))
                self.add_message(Message(role="assistant", content=content))

                return {
                    "content": content,
                    "usage": total_usage,
                }

        # 4) 达到 max_steps → 强制结束
        return {
            "content": f"已达到最大推理步数（{self.max_steps}），请简化您的问题或分步提问。",
            "usage": total_usage,
        }

    # ── 工具执行 ──────────────────────────────────────────────────

    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        执行工具调用。

        优先通过 ToolRegistry 执行（支持内置 + MCP 工具）。
        如果 ToolRegistry 不可用或工具未注册，返回错误信息。

        Args:
            tool_name: 工具名称
            args:      工具参数字典

        Returns:
            工具执行结果的文本表示
        """
        if self.tool_registry is None:
            return f"错误：Agent 未配置工具注册表，无法执行工具 '{tool_name}'"

        try:
            return await self.tool_registry.execute(tool_name, args)
        except ValueError as e:
            # 工具未注册
            return f"错误: {e}"
        except Exception as e:
            # 工具执行时发生未知错误
            return f"工具 '{tool_name}' 执行失败: {e}"
