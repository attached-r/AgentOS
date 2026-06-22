package com.agentos.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 注册 MCP 服务请求体
 */
@Data
public class CreateMcpServerReq {

    /** MCP 服务名称（唯一） */
    @NotBlank(message = "MCP 服务名称不能为空")
    private String name;

    /** 服务描述 */
    private String description;

    /** MCP 服务器端点地址 */
    @NotBlank(message = "端点地址不能为空")
    private String endpoint;

    /** 传输协议：sse / stdio，不传默认为 sse */
    private String transport;
}
