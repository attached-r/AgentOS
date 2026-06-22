package com.agentos.service;

import com.agentos.model.dto.CreateKnowledgeDocReq;
import com.agentos.model.entity.KnowledgeDoc;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.List;

/**
 * 知识库文档管理接口
 * <p>
 * 提供知识库文档的增删查、关键词搜索以及向量索引触发功能。
 * V2 MVP 阶段索引为占位实现，V3 将接入 Qdrant 向量检索。
 * </p>
 */
public interface KnowledgeDocService {

    /** 分页查询知识库文档，可按 Agent ID 过滤 */
    Page<KnowledgeDoc> page(int page, int size, Long agentId);

    /** 新增知识库文档 */
    KnowledgeDoc create(CreateKnowledgeDocReq req);

    /** 删除知识库文档 */
    void delete(Long id);

    /** 触发向量索引构建（V2 MVP 占位实现） */
    void triggerIndex(Long id);

    /** 关键词搜索文档（V2 修复：RAGPipeline 检索用，ILIKE 匹配标题和内容） */
    List<KnowledgeDoc> search(String q, int topK);
}
