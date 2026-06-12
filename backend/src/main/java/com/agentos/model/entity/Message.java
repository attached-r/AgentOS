package com.agentos.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("message")
public class Message {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long conversationId;

    private String role;

    private String content;

    private String metadata;

    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;
}
