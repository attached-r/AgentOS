package com.agentos.service;

import com.agentos.model.dto.CreateConversationReq;
import com.agentos.model.dto.SendMessageReq;
import com.agentos.model.dto.UpdateConversationReq;
import com.agentos.model.entity.Conversation;
import com.agentos.model.entity.Message;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.List;

public interface ConversationService {

    Conversation create(CreateConversationReq req);

    Page<Conversation> page(int page, int size);

    Page<Conversation> pageByAgent(Long agentId, int page, int size);

    List<Message> getMessages(Long conversationId);

    Message sendMessage(Long conversationId, SendMessageReq req);

    Conversation update(Long id, UpdateConversationReq req);

    void delete(Long id);
}
