package com.agentos.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.agentos.client.AgentRuntimeClient;
import com.agentos.common.BusinessException;
import com.agentos.mapper.AgentMapper;
import com.agentos.mapper.ConversationMapper;
import com.agentos.mapper.MessageMapper;
import com.agentos.model.dto.CreateConversationReq;
import com.agentos.model.dto.SendMessageReq;
import com.agentos.model.dto.UpdateConversationReq;
import com.agentos.model.entity.Agent;
import com.agentos.model.entity.Conversation;
import com.agentos.model.entity.Message;
import com.agentos.service.ConversationService;
import com.agentos.service.TaskLogService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ConversationServiceImpl implements ConversationService {

    private final ConversationMapper conversationMapper;
    private final MessageMapper messageMapper;
    private final AgentMapper agentMapper;
    private final AgentRuntimeClient agentRuntimeClient;
    private final ObjectMapper objectMapper;
    private final TaskLogService taskLogService;

    @Override
    public Conversation create(CreateConversationReq req) {
        if (req.getAgentId() == null) {
            throw new BusinessException("Agent ID 不能为空");
        }

        Agent agent = agentMapper.selectById(req.getAgentId());
        if (agent == null) {
            throw new BusinessException("Agent 不存在");
        }

        Conversation conversation = new Conversation();
        conversation.setTitle(req.getTitle());
        conversation.setAgentId(req.getAgentId());
        conversation.setUserId(StpUtil.getLoginIdAsLong());
        conversation.setStatus("active");
        conversationMapper.insert(conversation);
        return conversation;
    }

    @Override
    public Page<Conversation> page(int page, int size) {
        Long userId = StpUtil.getLoginIdAsLong();
        return conversationMapper.selectPage(
                new Page<>(page, size),
                new LambdaQueryWrapper<Conversation>()
                        .eq(Conversation::getUserId, userId)
                        .orderByDesc(Conversation::getUpdatedAt)
        );
    }

    @Override
    public Page<Conversation> pageByAgent(Long agentId, int page, int size) {
        Long userId = StpUtil.getLoginIdAsLong();
        return conversationMapper.selectPage(
                new Page<>(page, size),
                new LambdaQueryWrapper<Conversation>()
                        .eq(Conversation::getUserId, userId)
                        .eq(Conversation::getAgentId, agentId)
                        .orderByDesc(Conversation::getUpdatedAt)
        );
    }

    @Override
    public List<Message> getMessages(Long conversationId) {
        checkOwnership(conversationId);
        return messageMapper.selectList(
                new LambdaQueryWrapper<Message>()
                        .eq(Message::getConversationId, conversationId)
                        .orderByAsc(Message::getCreatedAt)
        );
    }

    @Override
    @Transactional
    public Message sendMessage(Long conversationId, SendMessageReq req) {
        if (req.getContent() == null || req.getContent().isBlank()) {
            throw new BusinessException("消息内容不能为空");
        }

        Conversation conversation = checkOwnership(conversationId);

        // 1. 保存用户消息
        Message userMessage = new Message();
        userMessage.setConversationId(conversationId);
        userMessage.setRole("user");
        userMessage.setContent(req.getContent());
        messageMapper.insert(userMessage);

        // 2. 获取全部消息作为上下文
        List<Message> history = messageMapper.selectList(
                new LambdaQueryWrapper<Message>()
                        .eq(Message::getConversationId, conversationId)
                        .orderByAsc(Message::getCreatedAt)
        );

        // 3. 调用 Python Runtime
        List<AgentRuntimeClient.MessagePayload> payloads = history.stream()
                .map(m -> new AgentRuntimeClient.MessagePayload(m.getRole(), m.getContent()))
                .collect(Collectors.toList());

        String taskId = "conv-" + conversationId + "-" + System.currentTimeMillis();
        taskLogService.info(taskId, conversation.getAgentId(), "开始调用 AI Runtime");

        AgentRuntimeClient.InvokeResponse response;
        try {
            response = agentRuntimeClient.invoke(conversation.getAgentId(), conversationId, payloads);
            taskLogService.info(taskId, conversation.getAgentId(), "AI Runtime 调用成功");
        } catch (Exception e) {
            taskLogService.error(taskId, conversation.getAgentId(), "调用失败: " + e.getMessage());
            throw new BusinessException("调用 AI Runtime 失败: " + e.getMessage());
        }

        // 4. 保存 assistant 回复
        Message assistantMessage = new Message();
        assistantMessage.setConversationId(conversationId);
        assistantMessage.setRole("assistant");
        assistantMessage.setContent(response.getContent());

        if (response.getUsage() != null) {
            try {
                assistantMessage.setMetadata(objectMapper.writeValueAsString(response.getUsage()));
            } catch (JsonProcessingException e) {
                assistantMessage.setMetadata("{}");
            }
        }

        messageMapper.insert(assistantMessage);
        return messageMapper.selectById(assistantMessage.getId());
    }

    @Override
    public Conversation update(Long id, UpdateConversationReq req) {
        Conversation conversation = checkOwnership(id);
        if (req.getTitle() != null) {
            conversation.setTitle(req.getTitle());
        }
        if (req.getStatus() != null) {
            conversation.setStatus(req.getStatus());
        }
        conversationMapper.updateById(conversation);
        return conversationMapper.selectById(id);
    }

    @Override
    public void delete(Long id) {
        Conversation conversation = checkOwnership(id);
        messageMapper.delete(new LambdaQueryWrapper<Message>()
                .eq(Message::getConversationId, id));
        conversationMapper.deleteById(id);
    }

    private Conversation checkOwnership(Long conversationId) {
        Conversation conversation = conversationMapper.selectById(conversationId);
        if (conversation == null) {
            throw new BusinessException("Conversation 不存在");
        }
        if (!conversation.getUserId().equals(StpUtil.getLoginIdAsLong())) {
            throw new BusinessException("无权操作该 Conversation");
        }
        return conversation;
    }
}
