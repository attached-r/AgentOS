package com.agentos.model.dto;

import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

/**
 * Agent 绑定工具请求体
 */
@Data
public class BindToolsReq {

    /** 要绑定的工具 ID 列表 */
    @NotEmpty(message = "工具 ID 列表不能为空")
    private List<Long> toolIds;
}
