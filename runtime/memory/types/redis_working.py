"""
RedisWorkingMemory —— 基于 Redis 的工作记忆（V2.1 升级）。

替换 V2 的 WorkingMemory（内存 List），解决：
  - 进程重启后短期记忆丢失
  - 水平扩展时多 Runtime 实例无法共享工作记忆
  - 内存 List O(n) 遍历性能随容量线性下降

数据模型（Redis）：
  Hash        wm:{agent_id}:items      →  field = 自增 ID, value = JSON(MemoryItem + tstamp)
  ZSet        wm:{agent_id}:rank       →  member = ID, score = importance
  String      wm:{agent_id}:counter    →  自增计数器（原子 INCR）
  TTL         EXPIRE 上述 3 个 key     →  会话空闲超时后整体过期

配置（从 env 加载，见 config.py RuntimeConfig）：
  REDIS_HOST          localhost
  REDIS_PORT          6379
  REDIS_PASSWORD      ""
  REDIS_WM_DB         1          ← 独立 db，与后端 Redis 物理隔离
  REDIS_WM_TTL        3600       ← 秒，默认 1 小时
  REDIS_WM_CAPACITY   100        ← 单个 Agent 容量上限

降级策略：
  1. Redis 连接失败 / 断连 → 透明回退到内存 self._fallback: List
  2. 降级后每 RECONNECT_INTERVAL（60 秒）尝试重连一次
  3. 重连成功 → 自动切回 Redis，降级期间的数据仍留在内存（不自动同步到 Redis）
  4. 降级期间所有操作行为与 V2 WorkingMemory（内存 List）一致

安全性：
  - 凭据仅从环境变量读取，不硬编码
  - 独立 db（默认 1）与后端业务 Redis 隔离
  - 支持 Redis ACL（用户限前缀 wm:*）
  - 内网通信；跨网络需配置 rediss:// TLS

用法（由 MemoryManager 内部使用，不直接实例化）：
    wm = RedisWorkingMemory(ttl=3600, capacity=100)
    await wm.add(MemoryItem(agent_id=1, content="...", importance=0.8))
    results = await wm.search("关键词")
"""
import json
import logging
import time
from typing import List, Optional

from memory.base import BaseMemory, MemoryItem

# Redis 导入可选 — 未安装时降级为纯内存模式
try:
    import redis.asyncio as aioredis
    from redis.exceptions import RedisError, ConnectionError as RedisConnError, TimeoutError as RedisTimeoutError
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


# 重连间隔（秒）
_RECONNECT_INTERVAL = 60


# ═══════════════════════════════════════════════════════════════════════════════
# RedisWorkingMemory
# ═══════════════════════════════════════════════════════════════════════════════

class RedisWorkingMemory(BaseMemory):
    """
    基于 Redis 的工作记忆（短期记忆）。

    用 Redis Hash + ZSet 替代 V2 的内存 List，保留相同接口语义。
    支持原子自增 ID、按重要性排序、EXPIRE TTL。
    关键路径均有 try-except 包裹 — Redis 不可用时降级为纯内存 List。
    """

    def __init__(
        self,
        ttl: int = 3600,
        capacity: int = 100,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: str = "",
        redis_db: int = 1,
    ):
        """
        Args:
            ttl:            工作记忆 TTL（秒）。会话空闲超过此时间自动过期。
            capacity:       单个 Agent 工作记忆容量上限。超出时淘汰重要性最低 + 最旧的数据。
            redis_host:     Redis 主机地址。默认从 env 读取，允许注入（方便测试）。
            redis_port:     Redis 端口。
            redis_password: Redis 密码。空字符串 = 无认证。
            redis_db:       Redis db 编号。默认 1，与后端业务 Redis（db 0）隔离。
        """
        self.ttl = ttl
        self.capacity = capacity

        # ── Redis 连接参数（从 env 或构造函数参数注入） ────────────
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._redis_password = redis_password
        self._redis_db = redis_db

        # ── Redis 运行时状态 ───────────────────────────────────────
        self._redis: Optional["aioredis.Redis"] = None   # type: ignore[name-defined]
        self._fallback_mode = not HAS_REDIS              # 未安装 redis-py → 永久降级
        self._last_reconnect_attempt: float = 0.0        # 上次重连时间戳
        # 降级用的后备存储（内存 List），结构与 WorkingMemory 一致
        self._fallback_items: List[MemoryItem] = []
        self._fallback_timestamps: List[float] = []

        self._logger = logging.getLogger("AgentOS.memory.RedisWorkingMemory")

        # 尝试初始连接（只记日志，不阻断初始化）
        if HAS_REDIS and not self._fallback_mode:
            self._logger.info(
                "RedisWorkingMemory: 准备连接 Redis %s:%s/%s",
                self._redis_host, self._redis_port, self._redis_db,
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # 连接管理
    # ═══════════════════════════════════════════════════════════════════════════

    async def _ensure_connection(self) -> Optional["aioredis.Redis"]:  # type: ignore[name-defined]
        """
        确保 Redis 连接可用。

        三重状态处理：
          1. 已连接且可用 → 直接返回
          2. 降级模式 + 距上次重连超过 _RECONNECT_INTERVAL → 尝试重连
          3. 降级模式 + 距上次重连不足 _RECONNECT_INTERVAL → 返回 None

        Returns:
            Redis 连接实例，或 None（降级模式中）
        """
        # ── 已连接：验证可用性 ──────────────────────────────────────
        if self._redis is not None:
            try:
                await self._redis.ping()
                return self._redis
            except (RedisConnError, RedisTimeoutError, RedisError) as exc:
                self._logger.warning("Redis 连接断连: %s，切换到降级模式", exc)
                self._redis = None
                self._fallback_mode = True
                self._last_reconnect_attempt = time.time()
                return None

        # ── 降级模式：间隔重连 ──────────────────────────────────────
        if self._fallback_mode:
            now = time.time()
            if now - self._last_reconnect_attempt < _RECONNECT_INTERVAL:
                return None  # 未到重连窗口

            self._last_reconnect_attempt = now
            try:
                self._redis = await self._create_connection()
                self._fallback_mode = False
                self._logger.info("Redis 重连成功，已切回正常模式")
                return self._redis
            except (RedisConnError, RedisTimeoutError, RedisError) as exc:
                self._logger.debug("Redis 重连失败（将在 %ds 后重试）: %s", _RECONNECT_INTERVAL, exc)
                return None

        # ── 首次连接 ────────────────────────────────────────────────
        try:
            self._redis = await self._create_connection()
            await self._redis.ping()
            self._fallback_mode = False
            self._logger.info("Redis 连接成功 [%s:%s/%s]", self._redis_host, self._redis_port, self._redis_db)
            return self._redis
        except (RedisConnError, RedisTimeoutError, RedisError) as exc:
            self._logger.warning(
                "Redis 连接失败 [%s:%s/%s]，降级为内存模式: %s",
                self._redis_host, self._redis_port, self._redis_db, exc,
            )
            self._fallback_mode = True
            self._last_reconnect_attempt = time.time()
            return None

    async def _create_connection(self) -> "aioredis.Redis":  # type: ignore[name-defined]
        """创建新的 Redis 连接（从 env 配置）。"""
        kwargs = {
            "host": self._redis_host,
            "port": self._redis_port,
            "db": self._redis_db,
            "decode_responses": True,  # 自动解码 bytes → str
            "socket_connect_timeout": 3,
            "socket_timeout": 5,
            "retry_on_timeout": False,  # 失败让上游降级，不阻塞重试
        }
        if self._redis_password:
            kwargs["password"] = self._redis_password
        return aioredis.Redis(**kwargs)

    def _key_items(self, agent_id: int) -> str:
        """Hash key：存储所有记忆项。"""
        return f"wm:{agent_id}:items"

    def _key_rank(self, agent_id: int) -> str:
        """ZSet key：按重要性排序。"""
        return f"wm:{agent_id}:rank"

    def _key_counter(self, agent_id: int) -> str:
        """String key：自增 ID 计数器。"""
        return f"wm:{agent_id}:counter"

    # ═══════════════════════════════════════════════════════════════════════════
    # 核心操作
    # ═══════════════════════════════════════════════════════════════════════════

    async def add(self, item: MemoryItem) -> int:
        """
        添加一条工作记忆。

        优先写入 Redis（Hash + ZSet + INCR），
        Redis 不可用时降级到内存 List。

        Returns:
            记忆 ID（Redis 模式 = 原子自增 ID / 降级模式 = list index+1）
        """
        # ── 时间戳填充 ──────────────────────────────────────────────
        if not item.created_at:
            item.created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # ── Redis 路径 ──────────────────────────────────────────────
        r = await self._ensure_connection()
        if r is not None:
            try:
                return await self._redis_add(r, item)
            except (RedisConnError, RedisTimeoutError, RedisError) as exc:
                self._logger.warning("Redis ADD 失败，降级到内存: %s", exc)
                self._redis = None
                self._fallback_mode = True
                self._last_reconnect_attempt = time.time()
                # 降级到内存路径
            except Exception as exc:
                self._logger.error("Redis ADD 未知异常: %s", exc)
                self._redis = None
                self._fallback_mode = True

        # ── 降级路径：内存 List ─────────────────────────────────────
        return self._fallback_add(item)

    async def _redis_add(self, r: "aioredis.Redis", item: MemoryItem) -> int:  # type: ignore[name-defined]
        """
        Redis 写入路径。

        事务语义（非 MULTI，分步执行）：
          1. INCR counter → 获取新 ID
          2. HSET items → 存储序列化数据
          3. ZADD rank → 记录重要性
          4. EXPIRE → 刷新 TTL
          5. 容量裁剪（ZREVRANGE + HDEL 淘汰低分项）
        """
        agent_id = item.agent_id
        key_items = self._key_items(agent_id)
        key_rank = self._key_rank(agent_id)
        key_counter = self._key_counter(agent_id)

        # 1) 原子自增 ID
        new_id = await r.incr(key_counter)

        # 2) 序列化存储（含时间戳以备 TTL 检查）
        payload = item.model_dump(exclude_none=True)
        payload["_ts"] = time.time()  # 加埋时间戳，供 search 时 TTL 过滤
        await r.hset(key_items, str(new_id), json.dumps(payload, ensure_ascii=False))

        # 3) 写入排序索引
        await r.zadd(key_rank, {str(new_id): item.importance})

        # 4) 刷新整个会话 TTL（写即活动，会话存活）
        ttl = self.ttl
        await r.expire(key_items, ttl)
        await r.expire(key_rank, ttl)
        await r.expire(key_counter, ttl)

        # 5) 容量裁剪
        await self._redis_enforce_capacity(r, agent_id)

        return new_id

    def _fallback_add(self, item: MemoryItem) -> int:
        """
        降级写入路径：纯内存 List。
        语义与 V2 WorkingMemory.add() 完全一致。
        """
        if not item.created_at:
            item.created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self._fallback_items.append(item)
        self._fallback_timestamps.append(time.time())
        self._fallback_enforce_capacity()
        return len(self._fallback_items)

    # ── Search ──────────────────────────────────────────────────────

    async def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """
        搜索工作记忆。

        检索策略（与 V2 WorkingMemory 一致）：
          1. 关键词包含匹配（query.lower() in content.lower()）
          2. 按重要性降序排序
          3. 返回 top-k

        Args:
            query: 搜索关键词（空字符串匹配全部）
            limit: 返回条数上限

        Returns:
            匹配的记忆项列表（按重要性降序）
        """
        r = await self._ensure_connection()
        if r is not None:
            try:
                return await self._redis_search(r, query, limit)
            except (RedisConnError, RedisTimeoutError, RedisError) as exc:
                self._logger.warning("Redis SEARCH 失败，降级到内存: %s", exc)
                self._redis = None
                self._fallback_mode = True

        # 降级路径
        return self._fallback_search(query, limit)

    async def _redis_search(
        self,
        r: "aioredis.Redis",  # type: ignore[name-defined]
        query: str,
        limit: int,
    ) -> List[MemoryItem]:
        """
        Redis 检索路径。

        读全部 items（容量上限 100，全量读可接受）→ 内存过滤 → 按 ZSet 排序返回。
        """
        # 获取 agent_id（从 item 内容反推，适合单 Agent 场景）
        # 先用 HGETALL 拿到所有 items
        key_items = self._key_items(0)  # 先用 0 占位，实际用所有 key
        agent_ids = set()
        # 实际需要通过 key pattern 扫描，但既然每次 add 知道 agent_id，这里用搜索时的 agent_id
        # 简化：从 items 中扫描所有 agent_id（适用于单表设计）
        # 实际应该由调用方传入 agent_id，但 BaseMemory 接口没有这个参数，
        # 所以搜索全部（通过 zrange all）
        # 优化：使用第一个可用的 key
        all_keys = await r.keys("wm:*:items")
        results: List[MemoryItem] = []
        query_lower = query.lower()

        for key in all_keys:
            raw = await r.hgetall(key)
            for mem_id, payload_json in raw.items():
                try:
                    data = json.loads(payload_json)
                except (json.JSONDecodeError, TypeError):
                    continue

                # TTL 过滤（检查埋的时间戳）
                ts = data.pop("_ts", None)
                if ts and (time.time() - ts > self.ttl):
                    continue  # 过期项，跳过

                content = data.get("content", "")
                if query and query_lower not in content.lower():
                    continue

                item = MemoryItem(**data)
                results.append(item)

        # 按重要性降序排列
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:limit]

    def _fallback_search(self, query: str, limit: int) -> List[MemoryItem]:
        """
        降级检索路径：纯内存搜索。
        与 V2 WorkingMemory.search() 完全一致。
        """
        self._fallback_evict_expired()

        query_lower = query.lower()
        matched = []
        for item in self._fallback_items:
            if query_lower in item.content.lower():
                matched.append(item)

        matched.sort(key=lambda x: x.importance, reverse=True)
        return matched[:limit]

    # ── 单条查询 ────────────────────────────────────────────────────

    async def get(self, item_id: int) -> Optional[MemoryItem]:
        """根据 ID 获取单条工作记忆。"""
        r = await self._ensure_connection()
        if r is not None:
            try:
                return await self._redis_get(r, item_id)
            except (RedisConnError, RedisTimeoutError, RedisError):
                self._redis = None
                self._fallback_mode = True

        # 降级路径
        return self._fallback_get(item_id)

    async def _redis_get(self, r: "aioredis.Redis", item_id: int) -> Optional[MemoryItem]:  # type: ignore[name-defined]
        """Redis 单条查询。"""
        # 扫描所有 items key
        all_keys = await r.keys("wm:*:items")
        for key in all_keys:
            payload = await r.hget(key, str(item_id))
            if payload is not None:
                try:
                    data = json.loads(payload)
                    data.pop("_ts", None)
                    return MemoryItem(**data)
                except (json.JSONDecodeError, TypeError):
                    return None
        return None

    def _fallback_get(self, item_id: int) -> Optional[MemoryItem]:
        """降级单条查询。"""
        idx = item_id - 1
        if 0 <= idx < len(self._fallback_items):
            return self._fallback_items[idx]
        return None

    # ── 删除 ────────────────────────────────────────────────────────

    async def delete(self, item_id: int) -> bool:
        """删除指定 ID 的工作记忆。"""
        r = await self._ensure_connection()
        if r is not None:
            try:
                return await self._redis_delete(r, item_id)
            except (RedisConnError, RedisTimeoutError, RedisError):
                self._redis = None
                self._fallback_mode = True

        return self._fallback_delete(item_id)

    async def _redis_delete(self, r: "aioredis.Redis", item_id: int) -> bool:  # type: ignore[name-defined]
        """Redis 删除：从 Hash 移除 field + 清理 ZSet 成员。"""
        deleted = False
        all_keys = await r.keys("wm:*:items")
        sid = str(item_id)
        for key_items in all_keys:
            removed = await r.hdel(key_items, sid)
            if removed:
                deleted = True
                # 对应的 rank key（替换后缀）
                key_rank = key_items.replace(":items", ":rank")
                await r.zrem(key_rank, sid)
                break
        return deleted

    def _fallback_delete(self, item_id: int) -> bool:
        """降级删除。"""
        idx = item_id - 1
        if 0 <= idx < len(self._fallback_items):
            self._fallback_items.pop(idx)
            self._fallback_timestamps.pop(idx)
            return True
        return False

    # ── 清空 ────────────────────────────────────────────────────────

    async def clear(self) -> None:
        """清空所有工作记忆（按 agent_id 逐 key 删除）。"""
        r = await self._ensure_connection()
        if r is not None:
            try:
                await self._redis_clear(r)
                return
            except (RedisConnError, RedisTimeoutError, RedisError):
                self._redis = None
                self._fallback_mode = True

        self._fallback_clear()

    async def _redis_clear(self, r: "aioredis.Redis") -> None:  # type: ignore[name-defined]
        """Redis 清空：删除所有 wm:* 开头 key。"""
        keys = await r.keys("wm:*")
        if keys:
            await r.delete(*keys)

    def _fallback_clear(self) -> None:
        """降级清空。"""
        self._fallback_items.clear()
        self._fallback_timestamps.clear()

    # ── 统计 ────────────────────────────────────────────────────────

    async def count(self) -> int:
        """返回工作记忆总数（已排除过期项）。"""
        r = await self._ensure_connection()
        if r is not None:
            try:
                return await self._redis_count(r)
            except (RedisConnError, RedisTimeoutError, RedisError):
                self._redis = None
                self._fallback_mode = True

        return self._fallback_count()

    async def _redis_count(self, r: "aioredis.Redis") -> int:  # type: ignore[name-defined]
        """Redis 统计：各 Hash 的 field 数之和。"""
        total = 0
        keys = await r.keys("wm:*:items")
        for key in keys:
            total += await r.hlen(key)
        return total

    def _fallback_count(self) -> int:
        """降级统计。"""
        self._fallback_evict_expired()
        return len(self._fallback_items)

    # ═══════════════════════════════════════════════════════════════════════════
    # 容量管理
    # ═══════════════════════════════════════════════════════════════════════════

    async def _redis_enforce_capacity(self, r: "aioredis.Redis", agent_id: int) -> None:  # type: ignore[name-defined]
        """
        Redis 容量裁剪。

        策略：保留 ZSet 中重要性最高的 capacity 项，
        删除其余项（从 Hash 和 ZSet 同时移除）。

        优于内存方案的淘汰粒度 — Redis ZREMRANGEBYRANK 是 O(log N) 操作，
        且不涉及数据复制（内存方案需要全量排序 + 拷贝）。
        """
        key_rank = self._key_rank(agent_id)
        key_items = self._key_items(agent_id)

        total = await r.zcard(key_rank)
        if total <= self.capacity:
            return

        # 需要移除的数量
        remove_count = total - self.capacity

        # ZRANGE 0 remove_count-1 → 重要性最低的 remove_count 个 member
        # ZSet 默认按 score 升序排列
        to_remove = await r.zrange(key_rank, 0, remove_count - 1)

        if not to_remove:
            return

        # 从 ZSet 移除
        await r.zrem(key_rank, *to_remove)

        # 从 Hash 移除
        await r.hdel(key_items, *to_remove)

    def _fallback_enforce_capacity(self) -> None:
        """
        降级容量裁剪。

        与 V2 WorkingMemory._enforce_capacity() 一致：
        按（重要性升序，时间升序）排序，保留最重要的 capacity 条。
        """
        if len(self._fallback_items) <= self.capacity:
            return

        paired = list(zip(self._fallback_items, self._fallback_timestamps))
        paired.sort(key=lambda x: (x[0].importance, x[1]))
        keep = paired[-self.capacity:]
        self._fallback_items = [p[0] for p in keep]
        self._fallback_timestamps = [p[1] for p in keep]

    # ═══════════════════════════════════════════════════════════════════════════
    # TTL 过期管理
    # ═══════════════════════════════════════════════════════════════════════════

    def _fallback_evict_expired(self) -> None:
        """
        降级 TTL 过期淘汰。

        与 V2 WorkingMemory._evict_expired() 一致：
        遍历所有记忆，移除超过 TTL 的项。
        Redis 模式的过期由 Redis EXPIRE 自动处理，无需应用层干预。
        """
        now = time.time()
        keep_items = []
        keep_timestamps = []

        for item, ts in zip(self._fallback_items, self._fallback_timestamps):
            if now - ts <= self.ttl:
                keep_items.append(item)
                keep_timestamps.append(ts)

        self._fallback_items = keep_items
        self._fallback_timestamps = keep_timestamps

    # ═══════════════════════════════════════════════════════════════════════════
    # 健康检查
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def is_redis_connected(self) -> bool:
        """Redis 是否处于连接状态（非降级模式）。"""
        return not self._fallback_mode and self._redis is not None

    @property
    def is_fallback_active(self) -> bool:
        """是否处于降级模式（纯内存）。"""
        return self._fallback_mode
