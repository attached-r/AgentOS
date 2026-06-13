package com.agentos.service;

import com.agentos.model.entity.Agent;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

public interface AgentService {

    Page<Agent> page(int page, int size);

    Agent getById(Long id);

    Agent create(Agent agent);

    Agent update(Agent agent);

    void delete(Long id);
}
