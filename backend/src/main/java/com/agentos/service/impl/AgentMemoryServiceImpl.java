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

/**
 * Agent 长期记忆管理实现
 * <p>
 * 记忆由 Python Runtime 在对话过程中自动提取保存，
 * 后端仅提供面向当前用户的查询和删除能力，确保数据隔离。
 * </p>
 */
@Service
@RequiredArgsConstructor
public class AgentMemoryServiceImpl implements AgentMemoryService {

    private final AgentMemoryMapper agentMemoryMapper;

    @Override
    public Page<AgentMemory> pageByAgent(Long agentId, int page, int size) {
        Long userId = StpUtil.getLoginIdAsLong();
        return agentMemoryMapper.selectPage(
                new Page<>(page, size),
                new LambdaQueryWrapper<AgentMemory>()
                        .eq(AgentMemory::getAgentId, agentId)
                        .eq(AgentMemory::getUserId, userId)
                        .orderByDesc(AgentMemory::getCreatedAt)
        );
    }

    @Override
    public AgentMemory getById(Long memId) {
        // V2 修复：EpisodicMemory.get() 通过此方法获取单条记忆
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
