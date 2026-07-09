package com.agentos.service;

import com.agentos.model.dto.CreateKnowledgeDocReq;
import com.agentos.model.entity.KnowledgeChunk;
import com.agentos.model.entity.KnowledgeDoc;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.List;

/**
 * 知识库文档管理接口
 * <p>
 * 提供知识库文档的增删查、Chunk 级关键词搜索以及向量索引触发功能。
 * V2 索引流程：调 Runtime split_document() 分块 → 存入 knowledge_chunk 表。
 * V3 将升级为 Qdrant 向量检索。
 * </p>
 */
public interface KnowledgeDocService {

    /** 分页查询知识库文档，可按 Agent ID 过滤 */
    Page<KnowledgeDoc> page(int page, int size, Long agentId);

    /** 新增知识库文档 */
    KnowledgeDoc create(CreateKnowledgeDocReq req);

    /** 删除知识库文档（级联删除关联 Chunk） */
    void delete(Long id);

    /**
     * 触发文档索引构建
     * <p>
     * V2 完整实现：调 Runtime split_document() 做分块 → 存入 knowledge_chunk 表。
     * 非幂等：重新索引时先清旧 chunk 再写新 chunk。
     * </p>
     */
    void triggerIndex(Long id);

    /**
     * Chunk 级关键词搜索（RAGPipeline._backend_search() 调用此方法）
     * <p>
     * 在 knowledge_chunk.content + title 上做 ILIKE 匹配，
     * 返回 Chunk 而非整篇文档，提高命中精度。
     * </p>
     */
    List<KnowledgeChunk> searchChunks(String q, int topK);
}
