package com.agentos.service.impl;

import com.agentos.client.AgentRuntimeClient;
import com.agentos.common.BusinessException;
import com.agentos.mapper.KnowledgeChunkMapper;
import com.agentos.mapper.KnowledgeDocMapper;
import com.agentos.model.dto.CreateKnowledgeDocReq;
import com.agentos.model.entity.KnowledgeChunk;
import com.agentos.model.entity.KnowledgeDoc;
import com.agentos.service.KnowledgeDocService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 知识库文档管理实现
 * <p>
 * V2 完整实现：triggerIndex 调 Runtime split_document() 分块后存入 knowledge_chunk 表，
 * searchChunks 在知识库分块上做 ILIKE 关键词匹配检索。
 * </p>
 */
@Service
@RequiredArgsConstructor
public class KnowledgeDocServiceImpl implements KnowledgeDocService {

    private final KnowledgeDocMapper knowledgeDocMapper;
    private final KnowledgeChunkMapper knowledgeChunkMapper;
    private final AgentRuntimeClient runtimeClient;

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
        // FK ON DELETE CASCADE 会自动清理 knowledge_chunk，但先显式删除更可靠
        knowledgeChunkMapper.deleteByDocId(id);
        knowledgeDocMapper.deleteById(id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void triggerIndex(Long id) {
        KnowledgeDoc doc = knowledgeDocMapper.selectById(id);
        if (doc == null) {
            throw new BusinessException("知识库文档不存在");
        }
        // 1) 标记为"索引中"
        doc.setEmbeddingStatus(1);
        knowledgeDocMapper.updateById(doc);

        try {
            // 2) 调 Runtime split_document() 做分块
            AgentRuntimeClient.ChunkResult result = runtimeClient.chunkDocument(doc.getContent(), doc.getTitle());
            List<AgentRuntimeClient.ChunkItem> items = result.getChunks();
            if (items == null || items.isEmpty()) {
                throw new BusinessException("文档分块结果为空");
            }

            // 3) 清旧 chunk → 写新 chunk（支持重新索引）
            knowledgeChunkMapper.deleteByDocId(id);
            for (AgentRuntimeClient.ChunkItem item : items) {
                KnowledgeChunk chunk = new KnowledgeChunk();
                chunk.setDocId(id);
                chunk.setContent(item.getContent());
                chunk.setSeq(item.getSeq());
                chunk.setTitle(item.getTitle() != null ? item.getTitle() : doc.getTitle());
                knowledgeChunkMapper.insert(chunk);
            }

            // 4) 更新文档状态
            doc.setChunkCount(items.size());
            doc.setEmbeddingStatus(2);
            knowledgeDocMapper.updateById(doc);

        } catch (Exception e) {
            // 索引失败，回退状态
            doc.setEmbeddingStatus(0);
            knowledgeDocMapper.updateById(doc);
            throw new BusinessException("文档索引失败: " + e.getMessage());
        }
    }

    @Override
    public List<KnowledgeChunk> searchChunks(String q, int topK) {
        // 在 knowledge_chunk.content + title 上做 ILIKE 匹配
        // 返回 Chunk 级结果，RAGPipeline._backend_search() 直接消费
        return knowledgeChunkMapper.searchByKeyword(q, Math.min(topK, 100));
    }
}
