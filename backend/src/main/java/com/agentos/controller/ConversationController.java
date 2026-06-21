package com.agentos.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import com.agentos.common.R;
import com.agentos.model.dto.CreateConversationReq;
import com.agentos.model.dto.SendMessageReq;
import com.agentos.model.dto.UpdateConversationReq;
import com.agentos.model.entity.Conversation;
import com.agentos.model.entity.Message;
import com.agentos.service.ConversationService;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/conversations")
@RequiredArgsConstructor
public class ConversationController {

    private final ConversationService conversationService;
    /**
     * 获取单个对话
     *
     * @param id 对话ID
     * @return 对话
     */
    @GetMapping("/{id}")
    @SaCheckLogin
    public R<Conversation> get(@PathVariable Long id) {
        return R.ok(conversationService.getById(id));
    }

    /**
     * 创建对话
     *
     * @param req 对话参数
     * @return 对话
     */
    @PostMapping
    @SaCheckLogin
    public R<Conversation> create(@Valid @RequestBody CreateConversationReq req) {
        return R.ok(conversationService.create(req));
    }
    /**
     * 获取所有对话
     *
     * @param page 页码
     * @param size 每页大小
     * @return 对话
     */
    @GetMapping
    @SaCheckLogin
    public R<Page<Conversation>> page(@RequestParam(defaultValue = "1") int page,
                                       @RequestParam(defaultValue = "10") int size) {
        return R.ok(conversationService.page(page, size));
    }
    /**
     * 获取对话消息
     *
     * @param id 对话id
     * @return 消息
     */
    @GetMapping("/{id}/messages")
    @SaCheckLogin
    public R<List<Message>> getMessages(@PathVariable Long id) {
        return R.ok(conversationService.getMessages(id));
    }
    /**
     * 发送消息
     *
     * @param id 对话id
     * @param req 消息参数
     * @return 消息
     */
    @PostMapping("/{id}/messages")
    @SaCheckLogin
    public R<Message> sendMessage(@PathVariable Long id,
                                   @Valid @RequestBody SendMessageReq req) {
        return R.ok(conversationService.sendMessage(id, req));
    }
    /**
     * 更新对话
     *
     * @param id 对话id
     * @param req 对话参数
     * @return 对话
     */
    @PutMapping("/{id}")
    @SaCheckLogin
    public R<Conversation> update(@PathVariable Long id,
                                   @RequestBody UpdateConversationReq req) {
        return R.ok(conversationService.update(id, req));
    }
    /**
     * 删除对话
     *
     * @param id 对话id
     * @return void
     */
    @DeleteMapping("/{id}")
    @SaCheckLogin
    public R<Void> delete(@PathVariable Long id) {
        conversationService.delete(id);
        return R.ok(null);
    }
}
