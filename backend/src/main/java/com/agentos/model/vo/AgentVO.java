package com.agentos.model.vo;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AgentVO {
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
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
