package com.agentos.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import com.agentos.common.R;
import com.agentos.model.dto.CreateKnowledgeDocReq;
import com.agentos.model.entity.AgentMemory;
import com.agentos.model.entity.KnowledgeDoc;
import com.agentos.service.AgentMemoryService;
import com.agentos.service.KnowledgeDocService;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 记忆中心控制器
 * <p>
 * 提供知识库文档管理和 Agent 长期记忆查看两个维度的 API。
 * 知识库管理：新增文档、文档列表、文档搜索、删除文档、触发向量索引
 * 记忆管理查看 Agent 的长期记忆列表、删除记忆
 * </p>
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class MemoryCenterController {

    private final KnowledgeDocService knowledgeDocService;
    private final AgentMemoryService agentMemoryService;

    // ==================== 知识库文档管理 ====================

    /**
     * 新增知识库文档
     *
     * @param req 文档参数
     * @return 新增成功的文档
     */
    @PostMapping("/knowledge/docs")
    @SaCheckLogin
    public R<KnowledgeDoc> createDoc(@Valid @RequestBody CreateKnowledgeDocReq req) {
        return R.ok(knowledgeDocService.create(req));
    }

    /**
     * 分页查询知识库文档列表
     *
     * @param page    页码
     * @param size    每页大小
     * @param agentId Agent ID（可选，按 Agent 过滤）
     * @return 文档分页数据
     */
    @GetMapping("/knowledge/docs")
    @SaCheckLogin
    public R<Page<KnowledgeDoc>> listDocs(@RequestParam(defaultValue = "1") int page,
                                           @RequestParam(defaultValue = "10") int size,
                                           @RequestParam(required = false) Long agentId) {
        return R.ok(knowledgeDocService.page(page, size, agentId));
    }

    /**
     * 搜索知识库文档（关键词匹配）
     * <p>
     * V2 修复：RAGPipeline._backend_search() 调用此端点进行检索，
     * 使用 PostgreSQL ILIKE 关键词匹配，返回 Top-K 匹配文档。
     * 此端点由 Python Runtime 的 RAGPipeline 调用，而非前端直接调用。
     * </p>
     *
     * @param q      搜索关键词
     * @param topK   返回条数上限
     * @return 匹配的文档列表
     */
    @GetMapping("/knowledge/docs/search")
    @SaCheckLogin
    public R<List<KnowledgeDoc>> searchDocs(@RequestParam String q,
                                             @RequestParam(defaultValue = "3") int topK) {
        return R.ok(knowledgeDocService.search(q, topK));
    }

    /**
     * 删除知识库文档
     *
     * @param id 文档 ID
     * @return 无数据
     */
    @DeleteMapping("/knowledge/docs/{id}")
    @SaCheckLogin
    public R<Void> deleteDoc(@PathVariable Long id) {
        knowledgeDocService.delete(id);
        return R.ok(null);
    }

    /**
     * 触发文档的向量索引构建
     * <p>
     * V2 MVP 阶段为占位实现，仅将文档状态标记为"索引中"。
     * 实际的向量索引构建将在 V3 接入 Qdrant 后完成。
     * </p>
     *
     * @param id 文档 ID
     * @return 无数据
     */
    @PostMapping("/knowledge/docs/{id}/index")
    @SaCheckLogin
    public R<Void> indexDoc(@PathVariable Long id) {
        knowledgeDocService.triggerIndex(id);
        return R.ok(null);
    }

    // ==================== Agent 长期记忆 ====================

    /**
     * 查询 Agent 的长期记忆列表
     * <p>
     * 记忆由 Python Runtime 在对话过程中自动提取，此处仅提供查看能力。
     * 返回结果已按当前登录用户过滤。
     * </p>
     *
     * @param id   Agent ID
     * @param page 页码
     * @param size 每页大小
     * @return 记忆分页数据
     */
    @GetMapping("/agents/{id}/memories")
    @SaCheckLogin
    public R<Page<AgentMemory>> listMemories(@PathVariable Long id,
                                              @RequestParam(defaultValue = "1") int page,
                                              @RequestParam(defaultValue = "10") int size) {
        return R.ok(agentMemoryService.pageByAgent(id, page, size));
    }

    /**
     * 获取单条记忆详情
     * <p>
     * V2 修复：EpisodicMemory.get() 调用的端点，之前缺失导致 404。
     * </p>
     *
     * @param memId 记忆 ID
     * @return 记忆详情
     */
    @GetMapping("/memories/{memId}")
    @SaCheckLogin
    public R<AgentMemory> getMemory(@PathVariable Long memId) {
        return R.ok(agentMemoryService.getById(memId));
    }

    /**
     * 删除 Agent 的某条记忆
     *
     * @param id    Agent ID
     * @param memId 记忆 ID
     * @return 无数据
     */
    @DeleteMapping("/agents/{id}/memories/{memId}")
    @SaCheckLogin
    public R<Void> deleteMemory(@PathVariable Long id, @PathVariable Long memId) {
        agentMemoryService.delete(id, memId);
        return R.ok(null);
    }
}
