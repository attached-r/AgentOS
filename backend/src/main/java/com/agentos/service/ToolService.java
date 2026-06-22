package com.agentos.service;

import com.agentos.model.entity.Tool;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.List;

/**
 * 工具管理接口
 * <p>
 * 提供全局工具查询、Agent-工具绑定/解绑等功能。
 * 内置工具（builtin）对所有 Agent 默认可用，无需绑定。
 * </p>
 */
public interface ToolService {

    /** 分页查询全局工具列表，可按来源类型（builtin / mcp）过滤 */
    Page<Tool> page(int page, int size, String source);

    /** 获取指定 Agent 已绑定的工具列表 */
    List<Tool> listByAgent(Long agentId);

    /** 为 Agent 绑定多个工具（已绑定的自动跳过） */
    void bindTools(Long agentId, List<Long> toolIds);

    /** 解绑 Agent 的某个工具 */
    void unbindTool(Long agentId, Long toolId);

    /** 获取 Agent 已绑定的启用中工具列表 */
    List<Tool> getEnabledToolsByAgent(Long agentId);
}
