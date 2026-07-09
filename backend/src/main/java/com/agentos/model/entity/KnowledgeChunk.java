package com.agentos.model.entity;

import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 知识库文档分块实体
 * <p>
 * 对应 knowledge_chunk 表，文档经分块后落此表。
 * 检索时按块匹配内容（而非整篇文档），提高命中精度。
 * 删除文档时通过 FK CASCADE 自动删除关联 chunk。
 * </p>
 */
@Data
@TableName("knowledge_chunk")
public class KnowledgeChunk {

    /** 主键 ID */
    @TableId(type = IdType.AUTO)
    private Long id;

    /** 所属文档 ID（FK → knowledge_doc.id，CASCADE） */
    private Long docId;

    /** 分块内容 */
    private String content;

    /** 块序号（文档内位置） */
    private Integer seq;

    /** 所属文档标题（冗余，方便展示和搜索） */
    private String title;

    /** 创建时间 */
    @TableField(insertStrategy = FieldStrategy.NEVER, updateStrategy = FieldStrategy.NEVER)
    private LocalDateTime createdAt;
}
