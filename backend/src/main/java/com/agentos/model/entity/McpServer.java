package com.agentos.model.entity;

import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * MCP 服务注册表实体
 * <p>
 * 对应 mcp_server 表，记录每个 MCP 服务器的连接信息。
 * 每个 MCP 服务器可提供一组工具（通过 tool 表关联）。
 * </p>
 */
@Data
@TableName("mcp_server")
public class McpServer {

    /** 主键 ID */
    @TableId(type = IdType.AUTO)
    private Long id;

    /** MCP 服务名称（唯一） */
    private String name;

    /** 服务描述 */
    private String description;

    /** MCP 服务器端点地址（URL 或命令） */
    private String endpoint;

    /** 传输协议：sse / stdio */
    private String transport;

    /** 状态：1=启用，0=禁用 */
    private Integer status;

    /** 创建时间 */
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;

    /** 更新时间 */
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime updatedAt;
}
