package com.agentos.model.dto;

import lombok.Data;

@Data
public class CreateConversationReq {
    private String title;
    private Long agentId;
}
