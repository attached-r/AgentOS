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

    @PostMapping
    @SaCheckLogin
    public R<Conversation> create(@Valid @RequestBody CreateConversationReq req) {
        return R.ok(conversationService.create(req));
    }

    @GetMapping
    @SaCheckLogin
    public R<Page<Conversation>> page(@RequestParam(defaultValue = "1") int page,
                                       @RequestParam(defaultValue = "10") int size) {
        return R.ok(conversationService.page(page, size));
    }

    @GetMapping("/{id}/messages")
    @SaCheckLogin
    public R<List<Message>> getMessages(@PathVariable Long id) {
        return R.ok(conversationService.getMessages(id));
    }

    @PostMapping("/{id}/messages")
    @SaCheckLogin
    public R<Message> sendMessage(@PathVariable Long id,
                                   @Valid @RequestBody SendMessageReq req) {
        return R.ok(conversationService.sendMessage(id, req));
    }

    @PutMapping("/{id}")
    @SaCheckLogin
    public R<Conversation> update(@PathVariable Long id,
                                   @RequestBody UpdateConversationReq req) {
        return R.ok(conversationService.update(id, req));
    }

    @DeleteMapping("/{id}")
    @SaCheckLogin
    public R<Void> delete(@PathVariable Long id) {
        conversationService.delete(id);
        return R.ok(null);
    }
}
