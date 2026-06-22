package com.agentos.model.entity;

import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * Agent 与工具的关联实体
 * <p>
 * 对应 agent_tool 表，记录 Agent 显式绑定了哪些 MCP 工具。
 * 内置工具（builtin）对所有 Agent 默认可用，不需要在此表记录。
 * UNIQUE(agent_id, tool_id) 约束防止重复绑定。
 * </p>
 */
@Data
@TableName("agent_tool")
public class AgentTool {

    /** 主键 ID */
    @TableId(type = IdType.AUTO)
    private Long id;

    /** Agent ID */
    private Long agentId;

    /** 工具 ID */
    private Long toolId;

    /** 创建时间 */
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;
}
