package com.agentos.service.impl;

import com.agentos.client.AgentRuntimeClient;
import com.agentos.client.AgentRuntimeClient.ToolSchema;
import com.agentos.common.BusinessException;
import com.agentos.mapper.McpServerMapper;
import com.agentos.mapper.ToolMapper;
import com.agentos.model.entity.McpServer;
import com.agentos.model.entity.Tool;
import com.agentos.service.McpSyncService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.util.List;

/**
 * MCP 工具同步服务实现
 * <p>
 * 核心同步流程：
 * 1. 调用 Runtime 的 MCP 同步接口，获取远程 MCP 服务器的工具列表
 * 2. 对每个工具的 schema 计算 SHA-256 version_hash
 * 3. 与数据库中已有记录对比，hash 未变则跳过，有变更或新增则写入
 * 4. 同步完成后将 MCP 服务标记为启用状态
 * </p>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class McpSyncServiceImpl implements McpSyncService {

    private final AgentRuntimeClient agentRuntimeClient;
    private final ToolMapper toolMapper;
    private final McpServerMapper mcpServerMapper;
    private final ObjectMapper objectMapper;

    @Override
    @Transactional
    public void sync(McpServer server) {
        try {
            // 1. 调用 Runtime 获取远程 MCP 服务器的工具列表
            List<ToolSchema> remoteTools = agentRuntimeClient.syncTools(
                    server.getEndpoint(), server.getTransport()
            );

            if (remoteTools == null || remoteTools.isEmpty()) {
                log.warn("MCP 服务 [{}] 同步结果为空，无工具注册", server.getName());
                return;
            }

            // 2. 遍历远程工具列表，执行 upsert
            for (ToolSchema remote : remoteTools) {
                // 将 schema 对象序列化为 JSON 字符串
                String schemaJson = objectMapper.writeValueAsString(remote.getSchema());
                // 归一化 JSON 后计算哈希（确保相同语义的 JSON 产生相同 hash）
                String normalizedJson = objectMapper.readTree(schemaJson).toString();
                String hash = computeVersionHash(normalizedJson);

                // 查询数据库中是否已存在同名工具
                Tool existing = toolMapper.selectOne(
                        new LambdaQueryWrapper<Tool>()
                                .eq(Tool::getMcpServerId, server.getId())
                                .eq(Tool::getName, remote.getName())
                );

                if (existing != null) {
                    // 只有 hash 变化时才更新
                    if (!hash.equals(existing.getVersionHash())) {
                        existing.setDescription(remote.getDescription());
                        existing.setSchema(schemaJson);
                        existing.setVersionHash(hash);
                        existing.setSyncedAt(LocalDateTime.now());
                        toolMapper.updateById(existing);
                        log.debug("工具 [{}] schema 已更新", remote.getName());
                    }
                } else {
                    // 新增工具
                    Tool tool = new Tool();
                    tool.setMcpServerId(server.getId());
                    tool.setName(remote.getName());
                    tool.setDescription(remote.getDescription());
                    tool.setSchema(schemaJson);
                    tool.setSource("mcp");
                    tool.setStatus(1);
                    tool.setVersionHash(hash);
                    tool.setSyncedAt(LocalDateTime.now());
                    toolMapper.insert(tool);
                    log.debug("工具 [{}] 已注册", remote.getName());
                }
            }

            // 3. 同步成功后将 MCP 服务标记为启用
            server.setStatus(1);
            mcpServerMapper.updateById(server);

            log.info("MCP 服务 [{}] 同步完成，共 {} 个工具", server.getName(), remoteTools.size());

        } catch (Exception e) {
            log.error("MCP 服务 [{}] 同步失败: {}", server.getName(), e.getMessage());
            throw new BusinessException("MCP 工具同步失败: " + e.getMessage());
        }
    }

    /**
     * 计算 SHA-256 哈希值（64 位十六进制字符串）
     *
     * @param input 输入字符串（归一化后的 JSON）
     * @return 哈希值
     */
    private String computeVersionHash(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(64);
            for (byte b : digest) {
                sb.append(String.format("%02x", b & 0xff));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new BusinessException("版本哈希计算失败");
        }
    }
}
