package com.agentos.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class InvokeAgentReq {
    @NotBlank(message = "prompt 不能为空")
    private String prompt;
}
