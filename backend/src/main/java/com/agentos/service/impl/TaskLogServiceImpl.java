package com.agentos.service.impl;

import com.agentos.mapper.TaskLogMapper;
import com.agentos.model.entity.TaskLog;
import com.agentos.service.TaskLogService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class TaskLogServiceImpl implements TaskLogService {

    private final TaskLogMapper taskLogMapper;

    @Override
    public void info(String taskId, Long agentId, String message) {
        save(taskId, agentId, "INFO", message);
    }

    @Override
    public void warn(String taskId, Long agentId, String message) {
        save(taskId, agentId, "WARN", message);
    }

    @Override
    public void error(String taskId, Long agentId, String message) {
        save(taskId, agentId, "ERROR", message);
    }

    @Override
    public Page<TaskLog> page(Long agentId, int page, int size) {
        LambdaQueryWrapper<TaskLog> wrapper = new LambdaQueryWrapper<TaskLog>()
                .orderByDesc(TaskLog::getCreatedAt);
        if (agentId != null) {
            wrapper.eq(TaskLog::getAgentId, agentId);
        }
        return taskLogMapper.selectPage(new Page<>(page, size), wrapper);
    }

    private void save(String taskId, Long agentId, String level, String message) {
        TaskLog log = new TaskLog();
        log.setTaskId(taskId);
        log.setAgentId(agentId);
        log.setLevel(level);
        log.setMessage(message);
        taskLogMapper.insert(log);
    }
}
