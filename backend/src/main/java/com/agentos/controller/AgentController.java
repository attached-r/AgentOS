package com.agentos.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import com.agentos.common.R;
import com.agentos.model.dto.CreateAgentReq;
import com.agentos.model.dto.InvokeAgentReq;
import com.agentos.model.dto.UpdateAgentReq;
import com.agentos.model.entity.Agent;
import com.agentos.model.entity.Conversation;
import com.agentos.service.AgentService;
import com.agentos.service.ConversationService;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/agents")
@RequiredArgsConstructor
public class AgentController {

    private final AgentService agentService;
    private final ConversationService conversationService;
    /**
     * 获取所有agents
     *
     * @return agents
     */
    @GetMapping
    @SaCheckLogin
    public R<Page<Agent>> page(@RequestParam(defaultValue = "1") int page,
                                @RequestParam(defaultValue = "10") int size) {
        return R.ok(agentService.page(page, size));
    }
    /**
     * 获取agent
     *
     * @param id agent id
     * @return agent
     */
    @GetMapping("/{id}")
    @SaCheckLogin
    public R<Agent> getById(@PathVariable Long id) {
        return R.ok(agentService.getById(id));
    }
    /**
     * 创建agent
     *
     * @param req agent
     * @return agent
     */
    @PostMapping
    @SaCheckLogin
    public R<Agent> create(@Valid @RequestBody CreateAgentReq req) {
        Agent agent = new Agent();
        BeanUtils.copyProperties(req, agent);
        return R.ok(agentService.create(agent));
    }
    /**
     * 更新agent
     *
     * @param id  agent id
     * @param req agent
     * @return agent
     */
    @PutMapping("/{id}")
    @SaCheckLogin
    public R<Agent> update(@PathVariable Long id, @RequestBody UpdateAgentReq req) {
        Agent agent = new Agent();
        BeanUtils.copyProperties(req, agent);
        agent.setId(id);
        return R.ok(agentService.update(agent));
    }
    /**
     * 删除agent
     *
     * @param id agent id
     * @return void
     */
    @DeleteMapping("/{id}")
    @SaCheckLogin
    public R<Void> delete(@PathVariable Long id) {
        agentService.delete(id);
        return R.ok(null);
    }
    /**
     * 调用agent
     *
     * @param id  agent id
     * @param req agent调用参数
     * @return agent调用结果
     */
    @PostMapping("/{id}/invoke")
    @SaCheckLogin
    public R<String> invoke(@PathVariable Long id, @Valid @RequestBody InvokeAgentReq req) {
        return R.ok(agentService.invoke(id, req.getPrompt()));
    }
    /**
     * 获取agent的对话记录
     *
     * @param id   agent id
     * @param page 页码
     * @param size 每页大小
     * @return agent的对话记录
     */
    @GetMapping("/{id}/conversations")
    @SaCheckLogin
    public R<Page<Conversation>> conversations(@PathVariable Long id,
                                                @RequestParam(defaultValue = "1") int page,
                                                @RequestParam(defaultValue = "10") int size) {
        return R.ok(conversationService.pageByAgent(id, page, size));
    }
}
