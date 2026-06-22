package com.agentos.service;

import com.agentos.model.entity.AgentMemory;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

/**
 * Agent 长期记忆管理接口
 * <p>
 * 提供记忆的查询、详情和删除功能。记忆由 Python Runtime 在对话过程中
 * 自动提取和保存，后端仅提供只读和删除接口供前端查看/管理。
 * </p>
 */
public interface AgentMemoryService {

    /** 分页查询 Agent 的长期记忆列表（已按当前用户过滤） */
    Page<AgentMemory> pageByAgent(Long agentId, int page, int size);

    /** 获取单条记忆详情（V2 修复：EpisodicMemory.get() 所需端点） */
    AgentMemory getById(Long memId);

    /** 删除指定的记忆记录（校验属主） */
    void delete(Long agentId, Long memId);
}
