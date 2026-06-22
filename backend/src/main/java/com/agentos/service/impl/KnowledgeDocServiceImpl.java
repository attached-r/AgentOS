package com.agentos.service.impl;

import com.agentos.common.BusinessException;
import com.agentos.mapper.KnowledgeDocMapper;
import com.agentos.model.dto.CreateKnowledgeDocReq;
import com.agentos.model.entity.KnowledgeDoc;
import com.agentos.service.KnowledgeDocService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 知识库文档管理实现
 * <p>
 * 提供文档的 CRUD、关键词搜索功能。triggerIndex 为 V2 MVP 占位实现，
 * 仅更新索引状态，实际向量索引构建将在 V3 中接入 Qdrant 后完成。
 * </p>
 */
@Service
@RequiredArgsConstructor
public class KnowledgeDocServiceImpl implements KnowledgeDocService {

    private final KnowledgeDocMapper knowledgeDocMapper;

    @Override
    public Page<KnowledgeDoc> page(int page, int size, Long agentId) {
        LambdaQueryWrapper<KnowledgeDoc> wrapper = new LambdaQueryWrapper<KnowledgeDoc>()
                .orderByDesc(KnowledgeDoc::getUpdatedAt);
        if (agentId != null) {
            wrapper.eq(KnowledgeDoc::getAgentId, agentId);
        }
        return knowledgeDocMapper.selectPage(new Page<>(page, size), wrapper);
    }

    @Override
    public KnowledgeDoc create(CreateKnowledgeDocReq req) {
        KnowledgeDoc doc = new KnowledgeDoc();
        BeanUtils.copyProperties(req, doc);
        if (doc.getSource() == null) {
            doc.setSource("manual");
        }
        doc.setChunkCount(0);
        doc.setEmbeddingStatus(0);
        knowledgeDocMapper.insert(doc);
        return knowledgeDocMapper.selectById(doc.getId());
    }

    @Override
    public void delete(Long id) {
        KnowledgeDoc doc = knowledgeDocMapper.selectById(id);
        if (doc == null) {
            throw new BusinessException("知识库文档不存在");
        }
        knowledgeDocMapper.deleteById(id);
    }

    @Override
    public void triggerIndex(Long id) {
        KnowledgeDoc doc = knowledgeDocMapper.selectById(id);
        if (doc == null) {
            throw new BusinessException("知识库文档不存在");
        }
        // V2 MVP：仅标记为"索引中"，实际向量索引构建由后续版本实现
        doc.setEmbeddingStatus(1);
        knowledgeDocMapper.updateById(doc);
    }

    @Override
    public List<KnowledgeDoc> search(String q, int topK) {
        // V2 修复：RAGPipeline 通过此方法检索知识库文档
        // 使用 PostgreSQL ILIKE 关键词匹配标题和内容
        LambdaQueryWrapper<KnowledgeDoc> wrapper = new LambdaQueryWrapper<KnowledgeDoc>()
                .like(KnowledgeDoc::getTitle, q)
                .or()
                .like(KnowledgeDoc::getContent, q)
                .orderByDesc(KnowledgeDoc::getUpdatedAt)
                .last("LIMIT " + topK);
        return knowledgeDocMapper.selectList(wrapper);
    }
}
