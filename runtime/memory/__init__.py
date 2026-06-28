# runtime/memory — 记忆系统
#
# V2 简化方案（三级记忆）：
#   - 工作记忆（Working）：当前会话的对话摘要，**Redis 存储**（V2.1 升级），
#     进程重启后保留，支持水平扩展共享。Redis 不可用时降级为内存 List。
#   - 情景记忆（Episodic）：跨会话的重要信息，通过后端 API 存到 PostgreSQL
#
# V3 才引入：
#   - 语义记忆（Semantic）
#   - Qdrant 向量检索
#
# 参考：../../说明文档/阶段v2.md 5.6 记忆系统
