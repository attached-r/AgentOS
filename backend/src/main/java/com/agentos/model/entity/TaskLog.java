package com.agentos.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("task_log")
public class TaskLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String taskId;

    private Long agentId;

    private String level;

    private String message;

    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;
}
