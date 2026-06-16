package com.agentos.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.List;

@Component
@RequiredArgsConstructor
public class AgentRuntimeClient {
    // http 客户端 连接runtime py后端
    private final RestTemplate restTemplate;

    @Value("${runtime.base-url}")
    private String baseUrl;
    /**
     * 调用运行时
     *
     * @param agentId          agent id
     * @param conversationId   conversation id
     * @param messages         messages
     * @return invoke response
     */
    public InvokeResponse invoke(Long agentId, Long conversationId, List<MessagePayload> messages) {
        String url = baseUrl + "/runtime/agents/" + agentId + "/invoke";

        InvokeRequest request = new InvokeRequest();
        request.setConversationId(conversationId);
        request.setMessages(messages);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<InvokeRequest> entity = new HttpEntity<>(request, headers);

        InvokeResponse response = restTemplate.postForObject(url, entity, InvokeResponse.class);
        if (response == null) {
            throw new RuntimeException("AI Runtime 返回为空");
        }
        return response;
    }
    /**
     * 同步agents
     *
     * @param agents agents
     */
    public void syncAgents(List<SyncAgentRequest> agents) {
        String url = baseUrl + "/runtime/agents/sync";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<List<SyncAgentRequest>> entity = new HttpEntity<>(agents, headers);
        restTemplate.postForObject(url, entity, String.class);
    }

    // 异步创建agent请求
    @Data
    public static class SyncAgentRequest {
        private Long id;
        private String name;
        private String description;
        @JsonProperty("system_prompt")
        private String systemPrompt;
        @JsonProperty("model_provider")
        private String modelProvider;
        @JsonProperty("model_name")
        private String modelName;
        private Double temperature;
        @JsonProperty("max_tokens")
        private Integer maxTokens;
    }
    // 请求
    @Data
    public static class InvokeRequest {
        private Long conversationId;
        private List<MessagePayload> messages;
    }
    // 消息载荷
    @Data
    public static class MessagePayload {
        private String role;
        private String content;

        public MessagePayload() {}

        public MessagePayload(String role, String content) {
            this.role = role;
            this.content = content;
        }
    }
    // 响应
    @Data
    public static class InvokeResponse {
        private String content;
        private Usage usage;
    }
    // 使用情况
    @Data
    public static class Usage {
        @JsonProperty("prompt_tokens") // Json 映射
        private Integer promptTokens;

        @JsonProperty("completion_tokens")
        private Integer completionTokens;

        @JsonProperty("total_tokens")
        private Integer totalTokens;
    }
}
