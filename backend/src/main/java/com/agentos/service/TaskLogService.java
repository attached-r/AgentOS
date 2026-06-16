package com.agentos.service;

import com.agentos.model.entity.TaskLog;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

public interface TaskLogService {

    void info(String taskId, Long agentId, String message);

    void warn(String taskId, Long agentId, String message);

    void error(String taskId, Long agentId, String message);

    Page<TaskLog> page(Long agentId, int page, int size);
}
