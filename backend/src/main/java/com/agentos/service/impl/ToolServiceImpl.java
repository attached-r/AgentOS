package com.agentos.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.agentos.common.BusinessException;
import com.agentos.mapper.AgentMapper;
import com.agentos.mapper.AgentToolMapper;
import com.agentos.mapper.ToolMapper;
import com.agentos.model.entity.Agent;
import com.agentos.model.entity.AgentTool;
import com.agentos.model.entity.Tool;
import com.agentos.service.ToolService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 工具管理实现
 * <p>
 * 提供工具查询和 Agent-工具绑定管理。
 * Agent-工具绑定涉及属主校验，确保用户只能操作自己的 Agent。
 * </p>
 */
@Service
@RequiredArgsConstructor
public class ToolServiceImpl implements ToolService {

    private final ToolMapper toolMapper;
    private final AgentToolMapper agentToolMapper;
    private final AgentMapper agentMapper;

    @Override
    public Page<Tool> page(int page, int size, String source) {
        LambdaQueryWrapper<Tool> wrapper = new LambdaQueryWrapper<Tool>()
                .orderByDesc(Tool::getCreatedAt);
        if (source != null && !source.isEmpty()) {
            wrapper.eq(Tool::getSource, source);
        }
        return toolMapper.selectPage(new Page<>(page, size), wrapper);
    }

    @Override
    public List<Tool> listByAgent(Long agentId) {
        // 通过 agent_tool 关联表查询 Agent 绑定的工具
        return toolMapper.selectList(
                new LambdaQueryWrapper<Tool>()
                        .inSql(Tool::getId,
                                "SELECT tool_id FROM agent_tool WHERE agent_id = " + agentId)
        );
    }

    @Override
    @Transactional
    public void bindTools(Long agentId, List<Long> toolIds) {
        // 校验 Agent 存在且属于当前用户
        Agent agent = agentMapper.selectById(agentId);
        if (agent == null) {
            throw new BusinessException("Agent 不存在");
        }
        if (!agent.getOwnerId().equals(StpUtil.getLoginIdAsLong())) {
            throw new BusinessException("无权操作该 Agent");
        }

        for (Long toolId : toolIds) {
            // 校验工具是否存在
            Tool tool = toolMapper.selectById(toolId);
            if (tool == null) {
                throw new BusinessException("工具 ID=" + toolId + " 不存在");
            }

            // 跳过已绑定的工具，保证幂等性
            Long count = agentToolMapper.selectCount(
                    new LambdaQueryWrapper<AgentTool>()
                            .eq(AgentTool::getAgentId, agentId)
                            .eq(AgentTool::getToolId, toolId)
            );
            if (count > 0) {
                continue;
            }

            AgentTool at = new AgentTool();
            at.setAgentId(agentId);
            at.setToolId(toolId);
            agentToolMapper.insert(at);
        }
    }

    @Override
    @Transactional
    public void unbindTool(Long agentId, Long toolId) {
        // 校验 Agent 存在且属于当前用户
        Agent agent = agentMapper.selectById(agentId);
        if (agent == null) {
            throw new BusinessException("Agent 不存在");
        }
        if (!agent.getOwnerId().equals(StpUtil.getLoginIdAsLong())) {
            throw new BusinessException("无权操作该 Agent");
        }

        agentToolMapper.delete(
                new LambdaQueryWrapper<AgentTool>()
                        .eq(AgentTool::getAgentId, agentId)
                        .eq(AgentTool::getToolId, toolId)
        );
    }

    @Override
    public List<Tool> getEnabledToolsByAgent(Long agentId) {
        // 查询 Agent 绑定且状态为启用的工具（用于对话时传入 Runtime）
        return toolMapper.selectList(
                new LambdaQueryWrapper<Tool>()
                        .eq(Tool::getStatus, 1)
                        .inSql(Tool::getId,
                                "SELECT tool_id FROM agent_tool WHERE agent_id = " + agentId)
        );
    }
}
