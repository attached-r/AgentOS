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
 * 工具实体
 * <p>
 * 对应 tool 表，记录 MCP 服务器提供或 Runtime 内置的工具。
 * mcpServerId 为 NULL 时表示内置工具（builtin），否则为 MCP 工具。
 * schema 字段存储 OpenAI function calling 格式的 JSON 定义。
 * </p>
 */
@Data
@TableName("tool")
public class Tool {

    /** 主键 ID */
    @TableId(type = IdType.AUTO)
    private Long id;

    /** 所属 MCP 服务器 ID（NULL = 内置工具） */
    private Long mcpServerId;

    /** 工具名称 */
    private String name;

    /** 工具描述 */
    private String description;

    /** OpenAI function calling schema（JSONB 格式） */
    @TableField(typeHandler = JsonbTypeHandler.class)
    private String schema;

    /** 来源：builtin / mcp */
    private String source;

    /** 状态：1=启用，0=禁用 */
    private Integer status;

    /** Schema 的 SHA-256 哈希，用于判断是否变更 */
    private String versionHash;

    /** 创建时间 */
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;

    /** 最近一次从 MCP 同步的时间 */
    private LocalDateTime syncedAt;
}
