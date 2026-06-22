package com.agentos.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 新增知识库文档请求体
 */
@Data
public class CreateKnowledgeDocReq {

    /** 关联的 Agent ID（为空表示全局文档） */
    private Long agentId;

    /** 文档标题 */
    private String title;

    /** 文档内容 */
    @NotBlank(message = "文档内容不能为空")
    private String content;

    /** 来源：manual / upload / web，不传默认为 manual */
    private String source;
}
