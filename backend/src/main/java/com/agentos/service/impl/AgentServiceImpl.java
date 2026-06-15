package com.agentos.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.agentos.client.AgentRuntimeClient;
import com.agentos.client.AgentRuntimeClient.SyncAgentRequest;
import com.agentos.common.BusinessException;
import com.agentos.mapper.AgentMapper;
import com.agentos.model.entity.Agent;
import com.agentos.service.AgentService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AgentServiceImpl implements AgentService {

    private final AgentMapper agentMapper;
    private final AgentRuntimeClient agentRuntimeClient;

    @Override
    public List<Agent> list() {
        return agentMapper.selectList(null);
    }

    @Override
    public Page<Agent> page(int page, int size) {
        // 1. 获取当前用户 ID
        Long userId = StpUtil.getLoginIdAsLong();
        // 2. 分页查询
        return agentMapper.selectPage(     // 分页参数，第一个参数为当前页，第二个参数为每页大小
                new Page<>(page, size),
                new LambdaQueryWrapper<Agent>()
                        .eq(Agent::getOwnerId, userId)
                        .orderByDesc(Agent::getUpdatedAt)  // 按更新时间倒序
        );
    }

    @Override
    public Agent getById(Long id) {
        Agent agent = agentMapper.selectById(id);
        if (agent == null) {
            throw new BusinessException("Agent 不存在");
        }
        return agent;
    }

    @Override
    public Agent create(Agent agent) {
        if (agent.getName() == null || agent.getName().isBlank()) {
            throw new BusinessException("Agent 名称不能为空");
        }
        agent.setId(null);// 设置 ID 为 null 因为MyBatis-Plus 会自动生成 ID
        agent.setOwnerId(StpUtil.getLoginIdAsLong());
        if (agent.getStatus() == null) {
            agent.setStatus(1);
        }
        agentMapper.insert(agent);
        return agent;
    }

    @Override
    public Agent update(Agent agent) {
        if (agent.getId() == null) {
            throw new BusinessException("id 不能为空");
        }
        Agent exist = agentMapper.selectById(agent.getId());
        if (exist == null) {
            throw new BusinessException("Agent 不存在");
        }
        if (!exist.getOwnerId().equals(StpUtil.getLoginIdAsLong())) {
            throw new BusinessException("无权操作该 Agent");
        }
        // 不允许修改 owner
        agent.setOwnerId(null);
        agentMapper.updateById(agent);
        return agentMapper.selectById(agent.getId());
    }

    @Override
    public void delete(Long id) {
        Agent agent = agentMapper.selectById(id);
        if (agent == null) {
            throw new BusinessException("Agent 不存在");
        }
        if (!agent.getOwnerId().equals(StpUtil.getLoginIdAsLong())) {
            throw new BusinessException("无权操作该 Agent");
        }
        agentMapper.deleteById(id);
    }

    @EventListener(ApplicationReadyEvent.class)
    public void syncAgentsToRuntime() {
        Exception lastException = null;
        for (int i = 0; i < 3; i++) {
            try {
                List<Agent> agents = agentMapper.selectList(null);
                List<SyncAgentRequest> syncList = agents.stream().map(a -> {
                    SyncAgentRequest r = new SyncAgentRequest();
                    r.setId(a.getId());
                    r.setName(a.getName());
                    r.setDescription(a.getDescription());
                    r.setSystemPrompt(a.getSystemPrompt());
                    r.setModelProvider(a.getModelProvider());
                    r.setModelName(a.getModelName());
                    r.setTemperature(a.getTemperature());
                    r.setMaxTokens(a.getMaxTokens());
                    return r;
                }).collect(Collectors.toList());
                agentRuntimeClient.syncAgents(syncList);
                log.info("syncAgentsToRuntime success, count={}", syncList.size());
                return;
            } catch (Exception e) {
                lastException = e;
                log.warn("syncAgentsToRuntime attempt {} failed: {}", i + 1, e.getMessage());
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException ignored) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
        log.warn("syncAgentsToRuntime failed after 3 retries (non-blocking): {}", lastException != null ? lastException.getMessage() : "unknown");
    }
}
