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

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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
     * @param apiKey           user-specific API key (optional)
     * @param userBaseUrl      user-specific base URL (optional)
     * @param tools            Agent 绑定的工具 schema 列表（V2 新增，可为空）
     * @return invoke response
     */
    public InvokeResponse invoke(Long agentId, Long conversationId, List<MessagePayload> messages,
                                  String apiKey, String userBaseUrl,
                                  List<Map<String, Object>> tools) {
        String url = this.baseUrl + "/runtime/agents/" + agentId + "/invoke";

        InvokeRequest request = new InvokeRequest();
        request.setConversationId(conversationId);
        request.setMessages(messages);
        request.setApiKey(apiKey);
        request.setBaseUrl(userBaseUrl);
        request.setTools(tools);   // V2 新增：携带工具上下文

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
     * 全量同步 Agent（仅启动时调用）
     *
     * @param agents 所有 Agent 列表
     */
    public void syncAgents(List<SyncAgentRequest> agents) {
        String url = baseUrl + "/runtime/agents/sync";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<List<SyncAgentRequest>> entity = new HttpEntity<>(agents, headers);
        restTemplate.postForObject(url, entity, String.class);
    }

    /**
     * 增量新增/更新单个 Agent（V2 优化：替代全量同步）
     *
     * @param agent 单个 Agent 配置
     */
    public void upsertAgent(SyncAgentRequest agent) {
        String url = baseUrl + "/runtime/agents/upsert";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<SyncAgentRequest> entity = new HttpEntity<>(agent, headers);
        restTemplate.postForObject(url, entity, String.class);
    }

    /**
     * 增量删除单个 Agent（V2 优化：替代全量同步）
     *
     * @param agentId 要删除的 Agent ID
     */
    public void deleteAgent(Long agentId) {
        String url = baseUrl + "/runtime/agents/" + agentId;
        restTemplate.delete(url);
    }

    /**
     * 同步 MCP 服务器的工具列表
     * <p>
     * 调用 Runtime 的 MCP 同步接口，让 Runtime 连接外部 MCP 服务器
     * 并拉取所有工具的 OpenAI function calling schema。
     * </p>
     *
     * @param endpoint  MCP 服务器端点地址
     * @param transport 传输协议（sse / stdio）
     * @return 工具 Schema 列表
     */
    public List<ToolSchema> syncTools(String endpoint, String transport) {
        String url = baseUrl + "/runtime/mcp/sync";

        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("endpoint", endpoint);
        requestBody.put("transport", transport);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        ToolSchema[] tools = restTemplate.postForObject(url, entity, ToolSchema[].class);
        if (tools == null) {
            throw new RuntimeException("MCP 工具同步返回为空");
        }
        return Arrays.asList(tools);
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
        private String apiKey;       // 用户自带的 API Key（可选，覆盖默认环境变量）
        private String baseUrl;      // 用户自定的 base URL（可选）
        private List<Map<String, Object>> tools;  // V2 新增：Agent 绑定的工具 schema 列表
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
        private List<Map<String, Object>> steps;  // V2 修复：工具调用步骤，由 Runtime 返回
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

    /**
     * 工具 Schema 定义
     * <p>
     * 对应 Runtime MCP 同步接口返回的单个工具定义。
     * schema 字段为 OpenAI function calling 格式的原始 JSON。
     * </p>
     */
    @Data
    public static class ToolSchema {
        /** 工具名称 */
        private String name;

        /** 工具描述 */
        private String description;

        /** OpenAI function calling schema（原始 JSON 对象） */
        private Object schema;
    }
}
