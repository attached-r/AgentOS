"""
Message 模型 —— 运行时内部统一的消息表示。

与后端约定的 wire format 保持一致：
  {"role": "user|assistant|system", "content": "..."}
Metadata 字段用于携带 token 用量、工具调用等额外信息（JSON 序列化）。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field

# 消息角色：与 OpenAI / 后端约定一致
MessageRole = Literal["user", "assistant", "system", "tool"]


class Message(BaseModel):
    """运行时内部消息模型。"""

    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, str]:
        """转成 wire format（后端 / LLM API 使用的格式）。"""
        return {"role": self.role, "content": self.content}


def messages_to_dicts(messages: List[Message]) -> List[Dict[str, str]]:
    """将 Message 列表批量转为 wire format。"""
    return [m.to_dict() for m in messages]


def dicts_to_messages(data: List[Dict[str, str]]) -> List[Message]:
    """将 wire format 的 dict 列表转回 Message 列表。"""
    return [Message(role=d["role"], content=d["content"]) for d in data]
