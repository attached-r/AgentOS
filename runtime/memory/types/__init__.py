# runtime/memory/types — 记忆类型实现
#
# 包含：
#   redis_working.py — 【V2.1】工作记忆（Redis 存储，EXPIRE TTL，自动降级到内存）
#   episodic.py      — 情景记忆（通过后端 API 持久化到 PostgreSQL）
#   working.py       — 工作记忆旧版（V2 内存 List，V2.1 起被 redis_working.py 替代）
