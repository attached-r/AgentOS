package com.agentos.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.agentos.client.AgentRuntimeClient;
import com.agentos.common.BusinessException;
import com.agentos.mapper.AgentMapper;
import com.agentos.mapper.ConversationMapper;
import com.agentos.mapper.MessageMapper;
import com.agentos.mapper.UserApiKeyMapper;
import com.agentos.model.dto.CreateConversationReq;
import com.agentos.model.dto.SendMessageReq;
import com.agentos.model.dto.UpdateConversationReq;
import com.agentos.model.entity.Agent;
import com.agentos.model.entity.Conversation;
import com.agentos.model.entity.Message;
import com.agentos.model.entity.UserApiKey;
import com.agentos.model.entity.Tool;
import com.agentos.service.ConversationService;
import com.agentos.service.TaskLogService;
import com.agentos.service.ToolService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ConversationServiceImpl implements ConversationService {

    private final ConversationMapper conversationMapper;
    private final MessageMapper messageMapper;
    private final AgentMapper agentMapper;
    private final UserApiKeyMapper userApiKeyMapper;
    private final AgentRuntimeClient agentRuntimeClient;
    private final ObjectMapper objectMapper;
    private final TaskLogService taskLogService;
    private final ToolService toolService;
    /**
     * 创建会话
     *
     * @param req 创建会话请求
     * @return 会话
     */
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

    /**
     * 分页获取会话列表
     *
     * @param page 页码
     * @param size 每页大小
     * @return 会话分页列表
     */
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
    /**
     * 根据 ID 获取会话（带所有权校验）
     */
    @Override
    public Conversation getById(Long id) {
        return checkOwnership(id);
    }

    /**
     * 分页获取指定 Agent 的会话列表
     *
     * @param agentId Agent ID
     * @param page    页码
     * @param size    每页大小
     * @return 会话分页列表
     */
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
    /**
     * 获取会话消息列表
     *
     * @param conversationId 会话 ID
     * @return 消息列表
     */
    @Override
    public List<Message> getMessages(Long conversationId) {
        checkOwnership(conversationId);
        return messageMapper.selectList(
                new LambdaQueryWrapper<Message>()
                        .eq(Message::getConversationId, conversationId)
                        .orderByAsc(Message::getCreatedAt)
        );
    }
    /**
     * 发送消息
     *
     * @param conversationId 会话 ID
     * @param req            发送消息请求
     * @return 发送的消息
     */
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

        // 3. 获取用户自带的 API Key（如有）
        Agent agent = agentMapper.selectById(conversation.getAgentId());
        String userApiKey = null;
        String userBaseUrl = null;
        if (agent != null) {
            UserApiKey key = userApiKeyMapper.selectOne(
                    new LambdaQueryWrapper<UserApiKey>()
                            .eq(UserApiKey::getUserId, StpUtil.getLoginIdAsLong())
                            .eq(UserApiKey::getProvider, agent.getModelProvider())
                            .eq(UserApiKey::getIsActive, 1)
            );
            if (key != null) {
                userApiKey = key.getApiKey();
                userBaseUrl = key.getBaseUrl();
            }
        }

        // 4. 获取 Agent 绑定的已启用 MCP 工具（V2 新增）
        List<Map<String, Object>> toolSchemas = null;
        try {
            List<Tool> agentTools = toolService.getEnabledToolsByAgent(conversation.getAgentId());
            if (!agentTools.isEmpty()) {
                toolSchemas = agentTools.stream()
                        .map(t -> {
                            try {
                                @SuppressWarnings("unchecked")
                                Map<String, Object> schemaMap = objectMapper.readValue(t.getSchema(), Map.class);
                                return schemaMap;
                            } catch (JsonProcessingException e) {
                                log.warn("工具 [{}] schema 解析失败: {}", t.getName(), e.getMessage());
                                return null;
                            }
                        })
                        .filter(Objects::nonNull)
                        .collect(Collectors.toList());
            }
        } catch (Exception e) {
            // 工具加载失败不阻塞对话，降级为无工具调用
            log.warn("加载 Agent 工具列表失败: {}", e.getMessage());
        }

        // 5. 调用 Python Runtime（携带工具上下文）
        List<AgentRuntimeClient.MessagePayload> payloads = history.stream()
                .map(m -> new AgentRuntimeClient.MessagePayload(m.getRole(), m.getContent()))
                .collect(Collectors.toList());

        String taskId = "conv-" + conversationId + "-" + System.currentTimeMillis();
        taskLogService.info(taskId, conversation.getAgentId(), "开始调用 AI Runtime");

        AgentRuntimeClient.InvokeResponse response;
        try {
            response = agentRuntimeClient.invoke(
                    conversation.getAgentId(), conversationId, payloads,
                    userApiKey, userBaseUrl, toolSchemas
            );
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

        // V2 修复：metadata 中同时存储 token 用量和工具调用步骤（供前端展示）
        try {
            Map<String, Object> meta = new java.util.HashMap<>();
            if (response.getUsage() != null) {
                meta.put("prompt_tokens", response.getUsage().getPromptTokens());
                meta.put("completion_tokens", response.getUsage().getCompletionTokens());
                meta.put("total_tokens", response.getUsage().getTotalTokens());
            }
            if (response.getSteps() != null && !response.getSteps().isEmpty()) {
                meta.put("steps", response.getSteps());
            }
            assistantMessage.setMetadata(objectMapper.writeValueAsString(meta.isEmpty() ? null : meta));
        } catch (JsonProcessingException e) {
            assistantMessage.setMetadata("{}");
        }

        messageMapper.insert(assistantMessage);
        return messageMapper.selectById(assistantMessage.getId());
    }
    /**
     * 更新会话
     *
     * @param id     会话 ID
     * @param req    更新请求
     * @return 更新后的会话
     */
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
    /**
     * 删除会话
     *
     * @param id 会话 ID
     */
    @Override
    public void delete(Long id) {
        Conversation conversation = checkOwnership(id);
        messageMapper.delete(new LambdaQueryWrapper<Message>()
                .eq(Message::getConversationId, id));
        conversationMapper.deleteById(id);
    }
    /**
     * 检查会话所有权
     *
     * @param conversationId 会话 ID
     * @return 会话
     */
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
