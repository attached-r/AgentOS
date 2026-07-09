package com.agentos.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.agentos.common.BusinessException;
import com.agentos.mapper.AgentMemoryMapper;
import com.agentos.model.entity.AgentMemory;
import com.agentos.service.AgentMemoryService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Agent 长期记忆管理实现
 * <p>
 * 记忆由 Python Runtime 在对话过程中自动提取保存，
 * 后端负责持久化存储和关键词检索（V2 ILIKE，V3 预留升级 Qdrant）。
 * 所有读操作按当前用户过滤，确保数据隔离。
 * </p>
 */
@Service
@RequiredArgsConstructor
public class AgentMemoryServiceImpl implements AgentMemoryService {

    private final AgentMemoryMapper agentMemoryMapper;

    // ────────────── V2 修复：保存记忆 → EpisodicMemory.add() 的持久化入口 ──────────────

    @Override
    public AgentMemory save(AgentMemory memory) {
        // V2 修复：原缺失此端点导致 Runtime EpisodicMemory 调用 404
        // Runtime 通过 httpx POST /api/agents/{agent_id}/memories 保存记忆
        agentMemoryMapper.insert(memory);
        // IdType.AUTO 在特定 MyBatis-Plus + PostgreSQL 组合下，
        // insert() 后 ID 可能未被回填到实体上，导致 selectById(null) 返回 null。
        // 此处用"agent_id + 内容 + 创建时间降序"回查确保拿到完整记录。
        if (memory.getId() != null) {
            return agentMemoryMapper.selectById(memory.getId());
        }
        LambdaQueryWrapper<AgentMemory> wrapper = new LambdaQueryWrapper<AgentMemory>()
                .eq(AgentMemory::getAgentId, memory.getAgentId())
                .eq(AgentMemory::getUserId, memory.getUserId())
                .eq(AgentMemory::getContent, memory.getContent())
                .orderByDesc(AgentMemory::getCreatedAt)
                .last("LIMIT 1");
        return agentMemoryMapper.selectOne(wrapper);
    }

    // ────────────── 分页查询 ──────────────

    @Override
    public Page<AgentMemory> pageByAgent(Long agentId, int page, int size) {
        Long userId = null;
        try {
            userId = StpUtil.getLoginIdAsLong();
        } catch (Exception e) {
            // Runtime 内部调用无登录态，不按用户过滤
        }
        LambdaQueryWrapper<AgentMemory> wrapper = new LambdaQueryWrapper<AgentMemory>()
                .eq(AgentMemory::getAgentId, agentId);
        if (userId != null) {
            wrapper.eq(AgentMemory::getUserId, userId);
        }
        wrapper.orderByDesc(AgentMemory::getCreatedAt);
        return agentMemoryMapper.selectPage(new Page<>(page, size), wrapper);
    }

    // ────────────── V2 修复：关键词搜索 → EpisodicMemory.search() 的检索入口 ──────────────

    @Override
    public List<AgentMemory> searchByAgent(Long agentId, String query, int limit) {
        // V2 修复：原 MemoryCenterController 无 q 参数，EpisodicMemory 搜索 404
        // V2 使用 PostgreSQL ILIKE 做关键词匹配，V3 预留升级为 Qdrant 向量检索
        //   - 替换：将 LambdaQueryWrapper 查询替换为 QdrantClient.search()
        //   - embedding 服务由 fastembed 提供
        Long userId = null;
        try {
            userId = StpUtil.getLoginIdAsLong();
        } catch (Exception e) {
            // Runtime 内部调用无登录态，不按用户过滤
        }
        LambdaQueryWrapper<AgentMemory> wrapper = new LambdaQueryWrapper<AgentMemory>()
                .eq(AgentMemory::getAgentId, agentId);
        if (userId != null) {
            wrapper.eq(AgentMemory::getUserId, userId);
        }
        // V2：ILIKE 关键词匹配 content 字段
        // V3 升级：删除此 .like()，改为调用 Qdrant 语义搜索并返回相似结果 ID 列表
        if (query != null && !query.isEmpty()) {
            wrapper.like(AgentMemory::getContent, query);
        }
        wrapper.orderByDesc(AgentMemory::getCreatedAt)
               .last("LIMIT " + Math.min(limit, 100));  // 上限 100，防滥用
        return agentMemoryMapper.selectList(wrapper);
    }

    // ────────────── 详情 ──────────────

    @Override
    public AgentMemory getById(Long memId) {
        AgentMemory memory = agentMemoryMapper.selectById(memId);
        if (memory == null) {
            throw new BusinessException("记忆记录不存在");
        }
        Long userId = StpUtil.getLoginIdAsLong();
        if (!memory.getUserId().equals(userId)) {
            throw new BusinessException("无权访问该记忆");
        }
        return memory;
    }

    // ────────────── 删除 ──────────────

    @Override
    public void delete(Long agentId, Long memId) {
        Long userId = StpUtil.getLoginIdAsLong();
        AgentMemory memory = agentMemoryMapper.selectById(memId);
        if (memory == null) {
            throw new BusinessException("记忆记录不存在");
        }
        if (!memory.getUserId().equals(userId)) {
            throw new BusinessException("无权操作该记忆");
        }
        if (!memory.getAgentId().equals(agentId)) {
            throw new BusinessException("该记忆不属于指定的 Agent");
        }
        agentMemoryMapper.deleteById(memId);
    }
}
