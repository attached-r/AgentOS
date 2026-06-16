"""
SimpleAgent —— V1 默认 Agent 实现。

执行策略：user msg → LLM → response
这是最简单的 Agent 模式，不涉及工具调用、多轮推理等复杂逻辑。

V1 核心原则：先跑通，再优化。
V2 会在此基础上增加 ReAct 循环、工具调用、流式输出等能力。
"""
from typing import Optional

from core.agent import BaseAgent
from core.llm import LLMClient
from core.message import Message


class SimpleAgent(BaseAgent):
    """
    简单对话 Agent —— V1 唯一使用的 Agent 实现。

    流程：
      1. 构建消息列表（system prompt + 历史 + 用户输入）
      2. 调用 LLM
      3. 保存用户消息和 assistant 回复到历史
      4. 返回回复内容

    用法：
        agent = SimpleAgent(name="助手", llm_client=llm, system_prompt="...")
        reply = await agent.run("你好")
    """

    def __init__(
        self,
        name: str,
        llm_client: LLMClient,
        system_prompt: Optional[str] = None,
    ):
        super().__init__(name, llm_client, system_prompt)

    async def run(self, input_text: str, **kwargs) -> str:
        """
        执行一次完整的用户消息处理。

        Args:
            input_text: 用户输入文本

        Returns:
            LLM 的回复文本
        """
        # 1) 构建完整消息列表
        messages = self.build_messages(input_text)

        # 2) 调用 LLM（system_prompt 已在 build_messages 中处理，这里不再重复传入）
        result = await self.llm_client.invoke(
            messages=messages,
            system_prompt=None,  # 已包含在 messages 中
        )

        # 3) 记录到历史
        self.add_message(Message(role="user", content=input_text))
        self.add_message(Message(role="assistant", content=result["content"]))

        # 4) 返回回复内容
        return result["content"]
