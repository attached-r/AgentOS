package com.agentos.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class CreateConversationReq {
    private String title;

    @NotNull(message = "Agent ID 不能为空")
    private Long agentId;
}
