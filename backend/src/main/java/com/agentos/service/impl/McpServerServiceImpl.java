package com.agentos.service.impl;

import com.agentos.common.BusinessException;
import com.agentos.mapper.McpServerMapper;
import com.agentos.model.dto.CreateMcpServerReq;
import com.agentos.model.dto.UpdateMcpServerReq;
import com.agentos.model.entity.McpServer;
import com.agentos.service.McpServerService;
import com.agentos.service.McpSyncService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

/**
 * MCP 服务管理实现
 * <p>
 * 处理 MCP 服务的 CRUD 操作，新建时会校验名称唯一性。
 * 同步操作委托给 McpSyncService 处理。
 * </p>
 */
@Service
@RequiredArgsConstructor
public class McpServerServiceImpl implements McpServerService {

    private final McpServerMapper mcpServerMapper;
    private final McpSyncService mcpSyncService;

    @Override
    public Page<McpServer> page(int page, int size) {
        return mcpServerMapper.selectPage(
                new Page<>(page, size),
                new LambdaQueryWrapper<McpServer>()
                        .orderByDesc(McpServer::getUpdatedAt)
        );
    }

    @Override
    public McpServer getById(Long id) {
        McpServer server = mcpServerMapper.selectById(id);
        if (server == null) {
            throw new BusinessException("MCP 服务不存在");
        }
        return server;
    }

    @Override
    public McpServer create(CreateMcpServerReq req) {
        // 校验名称唯一性
        Long count = mcpServerMapper.selectCount(
                new LambdaQueryWrapper<McpServer>()
                        .eq(McpServer::getName, req.getName())
        );
        if (count > 0) {
            throw new BusinessException("MCP 服务名称已存在");
        }

        McpServer server = new McpServer();
        BeanUtils.copyProperties(req, server);
        if (server.getTransport() == null) {
            server.setTransport("sse");
        }
        if (server.getStatus() == null) {
            server.setStatus(1);
        }
        mcpServerMapper.insert(server);
        return mcpServerMapper.selectById(server.getId());
    }

    @Override
    public McpServer update(Long id, UpdateMcpServerReq req) {
        McpServer server = mcpServerMapper.selectById(id);
        if (server == null) {
            throw new BusinessException("MCP 服务不存在");
        }

        // 更新传入的非空字段
        if (req.getName() != null) {
            // 如果名称变更，检查新名称的唯一性
            if (!req.getName().equals(server.getName())) {
                Long count = mcpServerMapper.selectCount(
                        new LambdaQueryWrapper<McpServer>()
                                .eq(McpServer::getName, req.getName())
                );
                if (count > 0) {
                    throw new BusinessException("MCP 服务名称已存在");
                }
            }
            server.setName(req.getName());
        }
        if (req.getDescription() != null) {
            server.setDescription(req.getDescription());
        }
        if (req.getEndpoint() != null) {
            server.setEndpoint(req.getEndpoint());
        }
        if (req.getTransport() != null) {
            server.setTransport(req.getTransport());
        }
        if (req.getStatus() != null) {
            server.setStatus(req.getStatus());
        }

        mcpServerMapper.updateById(server);
        return mcpServerMapper.selectById(id);
    }

    @Override
    public void delete(Long id) {
        McpServer server = mcpServerMapper.selectById(id);
        if (server == null) {
            throw new BusinessException("MCP 服务不存在");
        }
        // 数据库设置了 ON DELETE CASCADE，会级联删除关联的 tool 和 agent_tool 记录
        mcpServerMapper.deleteById(id);
    }

    @Override
    public void sync(Long id) {
        McpServer server = mcpServerMapper.selectById(id);
        if (server == null) {
            throw new BusinessException("MCP 服务不存在");
        }
        mcpSyncService.sync(server);
    }
}
