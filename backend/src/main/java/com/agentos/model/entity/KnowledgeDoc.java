package com.agentos.model.entity;

import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 知识库文档实体
 * <p>
 * 对应 knowledge_doc 表，记录上传或手动录入的知识文档。
 * 文档可关联到特定 Agent（agentId 不为空）或全局可用（agentId 为空）。
 * embeddingStatus 追踪向量索引构建状态：0=未索引，1=索引中，2=已索引。
 * </p>
 */
@Data
@TableName("knowledge_doc")
public class KnowledgeDoc {

    /** 主键 ID */
    @TableId(type = IdType.AUTO)
    private Long id;

    /** 关联的 Agent ID（NULL = 全局文档） */
    private Long agentId;

    /** 文档标题 */
    private String title;

    /** 文档内容 */
    private String content;

    /** 来源：manual / upload / web */
    private String source;

    /** 分块数量 */
    private Integer chunkCount;

    /** 向量索引状态：0=未索引，1=索引中，2=已索引 */
    private Integer embeddingStatus;

    /** 创建时间 */
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;

    /** 更新时间 */
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime updatedAt;
}
