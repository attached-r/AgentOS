"""
Context —— 上下文构建模块（V2 新增）。

仿照 hello_agents 的 GSSC（Gather → Structure）模式，
将分散的信息源（system prompt、记忆、RAG）汇集为结构化上下文。

核心组件：
  - ContextBuilder:  上下文构建器（Gather → Structure）
  - ContextPacket:   候选信息包（GSSC 流动单元）
  - ContextConfig:   构建配置
"""
from context.builder import ContextBuilder, ContextPacket, ContextConfig

__all__ = ["ContextBuilder", "ContextPacket", "ContextConfig"]
