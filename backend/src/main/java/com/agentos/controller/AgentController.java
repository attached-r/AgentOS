package com.agentos.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import com.agentos.common.R;
import com.agentos.model.entity.Agent;
import com.agentos.service.AgentService;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/agents")
@RequiredArgsConstructor
public class AgentController {

    private final AgentService agentService;

    @GetMapping
    @SaCheckLogin  // 登录认证
    public R<Page<Agent>> page(@RequestParam(defaultValue = "1") int page,
                                @RequestParam(defaultValue = "10") int size) {
        return R.ok(agentService.page(page, size));
    }

    @GetMapping("/{id}")
    @SaCheckLogin
    public R<Agent> getById(@PathVariable Long id) {
        return R.ok(agentService.getById(id));
    }

    @PostMapping
    @SaCheckLogin
    public R<Agent> create(@RequestBody Agent agent) {
        return R.ok(agentService.create(agent));
    }

    @PutMapping("/{id}")
    @SaCheckLogin
    public R<Agent> update(@PathVariable Long id, @RequestBody Agent agent) {
        agent.setId(id);
        return R.ok(agentService.update(agent));
    }

    @DeleteMapping("/{id}")
    @SaCheckLogin
    public R<Void> delete(@PathVariable Long id) {
        agentService.delete(id);
        return R.ok(null);
    }
}
