"""
Agent 基类 —— 所有 Agent 实现的抽象基类。

职责：
  1. 定义 Agent 生命周期（初始化 → run → 获取结果）
  2. 管理对话历史（_history 列表）
  3. 提供消息构建的骨架方法
  4. run() 为抽象方法，子类必须实现不同的执行策略

V1 子类：SimpleAgent（直接调用 LLM）
V2 子类：ReActAgent（多轮推理 + 工具调用）、ReflectionAgent 等
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .message import Message
from .llm import LLMClient


class BaseAgent(ABC):
    """
    Agent 抽象基类。

    所有 Agent 类型必须实现 run() 方法。
    """

    def __init__(
        self,
        name: str,
        llm_client: LLMClient,
        system_prompt: Optional[str] = None,
        tool_registry: Optional["ToolRegistry"] = None,  # ← V2 新增：工具注册表
    ):
        self.name = name
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.tool_registry = tool_registry  # V2 新增
        self._history: List[Message] = []

    # ------------------------------------------------------------------
    # 子类必须实现的抽象方法
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(self, input_text: str, **kwargs) -> str:
        """处理用户输入，返回最终回复内容。"""
        ...

    # ------------------------------------------------------------------
    # 历史管理
    # ------------------------------------------------------------------

    def add_message(self, message: Message) -> None:
        """添加消息到历史记录。"""
        self._history.append(message)

    def clear_history(self) -> None:
        """清空历史记录。"""
        self._history.clear()

    def get_history(self) -> List[Message]:
        """获取历史记录（返回副本，防止外部修改）。"""
        return self._history.copy()

    # ------------------------------------------------------------------
    # 消息构建
    # ------------------------------------------------------------------

    def build_messages(self, user_query: str) -> List[Dict[str, str]]:
        """
        构建发给 LLM 的完整消息列表。

        顺序：system prompt → 对话历史 → 当前用户输入
        """
        messages: List[Dict[str, str]] = []

        # 1) system prompt
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        # 2) 对话历史
        for msg in self._history:
            messages.append(msg.to_dict())

        # 3) 当前用户输入
        messages.append({"role": "user", "content": user_query})

        return messages

    def __str__(self) -> str:
        return f"BaseAgent(name={self.name})"
