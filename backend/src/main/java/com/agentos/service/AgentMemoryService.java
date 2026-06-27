package com.agentos.service;

import com.agentos.model.entity.AgentMemory;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.List;

/**
 * Agent 长期记忆管理接口
 * <p>
 * 提供记忆的保存、查询、详情和删除功能。记忆由 Python Runtime 在对话过程中
 * 自动提取和保存，后端负责持久化存储和检索（V2 使用 PostgreSQL ILIKE，
 * V3 预留升级为 Qdrant 向量检索）。
 * </p>
 */
public interface AgentMemoryService {

    /** 保存一条长期记忆（由 Runtime 的 MemoryManager 调用） */
    AgentMemory save(AgentMemory memory);

    /** 分页查询 Agent 的长期记忆列表（已按当前用户过滤） */
    Page<AgentMemory> pageByAgent(Long agentId, int page, int size);

    /**
     * 关键词搜索 Agent 的长期记忆（V2 使用 ILIKE，V3 升级向量检索）
     * 由 Runtime 的 EpisodicMemory.search() 调用
     */
    List<AgentMemory> searchByAgent(Long agentId, String query, int limit);

    /** 获取单条记忆详情 */
    AgentMemory getById(Long memId);

    /** 删除指定的记忆记录（校验属主） */
    void delete(Long agentId, Long memId);
}
