package com.agentos.service;

import com.agentos.model.dto.CreateMcpServerReq;
import com.agentos.model.dto.UpdateMcpServerReq;
import com.agentos.model.entity.McpServer;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

/**
 * MCP 服务管理接口
 * <p>
 * 提供 MCP 服务的注册、查询、更新、删除以及工具同步功能。
 * </p>
 */
public interface McpServerService {

    /** 分页查询 MCP 服务列表 */
    Page<McpServer> page(int page, int size);

    /** 根据 ID 获取 MCP 服务 */
    McpServer getById(Long id);

    /** 注册新的 MCP 服务 */
    McpServer create(CreateMcpServerReq req);

    /** 更新 MCP 服务信息 */
    McpServer update(Long id, UpdateMcpServerReq req);

    /** 删除 MCP 服务（级联删除关联的工具和绑定关系） */
    void delete(Long id);

    /** 同步 MCP 服务的工具列表（调用 Runtime 拉取最新 schema） */
    void sync(Long id);
}
