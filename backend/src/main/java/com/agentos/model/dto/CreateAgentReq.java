package com.agentos.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CreateAgentReq {
    @NotBlank(message = "Agent 名称不能为空")
    private String name;

    private String description;

    @NotBlank(message = "系统提示词不能为空")
    private String systemPrompt;

    private String modelProvider;
    private String modelName;
    private Double temperature;
    private Integer maxTokens;
    private String avatarUrl;
}
