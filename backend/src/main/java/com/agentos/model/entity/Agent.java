package com.agentos.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("agent")
public class Agent {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String description;

    private String systemPrompt;

    private String modelProvider;

    private String modelName;

    private Double temperature;

    private Integer maxTokens;

    private String avatarUrl;

    private Long ownerId;

    private Integer status;

    // FieldStrategy.NEVER 表示该字段不允许插入和更新
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;

    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime updatedAt;
}
