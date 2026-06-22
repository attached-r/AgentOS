package com.agentos.service;

import com.agentos.model.entity.McpServer;

/**
 * MCP 工具同步服务接口
 * <p>
 * 负责调用 Python Runtime 连接外部 MCP 服务器，拉取工具列表，
 * 并将工具 Schema 存入 tool 表。同步时通过 version_hash
 * 判断 schema 是否变更，避免无效更新。
 * </p>
 */
public interface McpSyncService {

    /**
     * 同步指定 MCP 服务器的工具列表
     *
     * @param server MCP 服务器实体
     */
    void sync(McpServer server);
}
