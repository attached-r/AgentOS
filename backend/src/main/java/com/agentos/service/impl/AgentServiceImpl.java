package com.agentos.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.agentos.client.AgentRuntimeClient;
import com.agentos.client.AgentRuntimeClient.SyncAgentRequest;
import com.agentos.common.BusinessException;
import com.agentos.mapper.AgentMapper;
import com.agentos.model.entity.Agent;
import com.agentos.service.AgentService;
import com.agentos.service.TaskLogService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.databind.ObjectMapper;
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
    private final ObjectMapper objectMapper;
    private final TaskLogService taskLogService;

    @Override
    public List<Agent> list() {
        return agentMapper.selectList(null);
    }

    @Override
    public Page<Agent> page(int page, int size) {
        Long userId = StpUtil.getLoginIdAsLong();
        return agentMapper.selectPage(
                new Page<>(page, size),
                new LambdaQueryWrapper<Agent>()
                        .eq(Agent::getOwnerId, userId)
                        .orderByDesc(Agent::getUpdatedAt)
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
        agent.setId(null);
        agent.setOwnerId(StpUtil.getLoginIdAsLong());
        if (agent.getStatus() == null) {
            agent.setStatus(1);
        }
        agentMapper.insert(agent);
        // V2 优化：增量 upsert，不再全量同步
        upsertAgentToRuntime(agentMapper.selectById(agent.getId()));
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
        agent.setOwnerId(null);
        agentMapper.updateById(agent);
        // V2 优化：增量 upsert，不再全量同步
        upsertAgentToRuntime(agentMapper.selectById(agent.getId()));
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
        // V2 优化：增量 delete，不再全量同步
        deleteAgentFromRuntime(id);
    }
    // 调用 Agent
    @Override
    public String invoke(Long id, String prompt) {
        if (prompt == null || prompt.isBlank()) {
            throw new BusinessException("prompt 不能为空");
        }
        Agent agent = getById(id);

        List<AgentRuntimeClient.MessagePayload> messages = List.of(
                new AgentRuntimeClient.MessagePayload("user", prompt)
        );

        String taskId = "invoke-" + id + "-" + System.currentTimeMillis();
        taskLogService.info(taskId, id, "开始直接调用 Agent");

        AgentRuntimeClient.InvokeResponse response;
        try {
            response = agentRuntimeClient.invoke(id, null, messages, null, null, null);
            taskLogService.info(taskId, id, "Agent 调用成功");
        } catch (Exception e) {
            taskLogService.error(taskId, id, "调用失败: " + e.getMessage());
            throw new BusinessException("调用 Agent 失败: " + e.getMessage());
        }
        return response.getContent();
    }
    // ── 增量同步（CRUD 用） ─────────────────────────────────────

    private void upsertAgentToRuntime(Agent agent) {
        // V2 优化：仅推送单个 Agent，避免全量查询和传输
        try {
            SyncAgentRequest r = toSyncRequest(agent);
            agentRuntimeClient.upsertAgent(r);
        } catch (Exception e) {
            log.warn("upsertAgent failed: {}", e.getMessage());
        }
    }

    private void deleteAgentFromRuntime(Long agentId) {
        // V2 优化：仅推送删除 ID，避免全量查询和传输
        try {
            agentRuntimeClient.deleteAgent(agentId);
        } catch (Exception e) {
            log.warn("deleteAgent failed: {}", e.getMessage());
        }
    }

    // ── 全量同步（启动时用） ─────────────────────────────────────

    // 应用启动时全量同步 Agents 到 Runtime
    @EventListener(ApplicationReadyEvent.class)
    public void syncAgentsToRuntime() {
        Exception lastException = null;
        for (int i = 0; i < 3; i++) {
            try {
                List<Agent> agents = agentMapper.selectList(null);
                List<SyncAgentRequest> syncList = agents.stream()
                        .map(this::toSyncRequest)
                        .collect(Collectors.toList());
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

    private SyncAgentRequest toSyncRequest(Agent a) {
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
    }
}
