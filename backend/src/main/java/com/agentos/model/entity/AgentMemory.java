package com.agentos.model.entity;

import com.agentos.common.JsonbTypeHandler;
import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * Agent 长期记忆实体
 * <p>
 * 对应 agent_memory 表，记录从对话中提取的重要信息。
 * 记忆类型分为：working（工作记忆）、episodic（情景记忆）、semantic（语义记忆）。
 * V2 简化实现，主要用于跨会话的长期记忆存储与检索。
 * </p>
 */
@Data
@TableName("agent_memory")
public class AgentMemory {

    /** 主键 ID */
    @TableId(type = IdType.AUTO)
    private Long id;

    /** 关联的 Agent ID */
    private Long agentId;

    /** 所属用户 ID */
    private Long userId;

    /** 记忆类型：working / episodic / semantic */
    private String memoryType;

    /** 记忆内容 */
    private String content;

    /** 重要程度（0.0 ~ 1.0） */
    private Double importance;

    /** 额外元数据（JSONB 格式） */
    @TableField(typeHandler = JsonbTypeHandler.class)
    private String metadata;

    /** 创建时间 */
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;
}
