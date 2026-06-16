package com.agentos.service;

import com.agentos.model.entity.Agent;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.List;

public interface AgentService {

    List<Agent> list();

    Page<Agent> page(int page, int size);

    Agent getById(Long id);

    Agent create(Agent agent);

    Agent update(Agent agent);

    void delete(Long id);

    /**
     * 直接调用 Agent（不经过 Conversation）
     *
     * @param id     agent id
     * @param prompt 用户输入
     * @return 调用结果内容
     */
    String invoke(Long id, String prompt);
}
