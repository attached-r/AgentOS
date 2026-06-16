package com.agentos.model.dto;

import lombok.Data;

@Data
public class UpdateAgentReq {
    private String name;
    private String description;
    private String systemPrompt;
    private String modelProvider;
    private String modelName;
    private Double temperature;
    private Integer maxTokens;
    private String avatarUrl;
    private Integer status;
}
