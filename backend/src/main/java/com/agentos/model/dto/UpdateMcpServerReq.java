package com.agentos.model.dto;

import lombok.Data;

/**
 * 更新 MCP 服务请求体
 * <p>
 * 所有字段可选，仅更新传入的非空字段。
 * </p>
 */
@Data
public class UpdateMcpServerReq {

    /** MCP 服务名称 */
    private String name;

    /** 服务描述 */
    private String description;

    /** 端点地址 */
    private String endpoint;

    /** 传输协议 */
    private String transport;

    /** 状态：1=启用，0=禁用 */
    private Integer status;
}
