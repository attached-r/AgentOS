package com.agentos.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import com.agentos.common.R;
import com.agentos.model.dto.BindToolsReq;
import com.agentos.model.dto.CreateMcpServerReq;
import com.agentos.model.dto.UpdateMcpServerReq;
import com.agentos.model.entity.McpServer;
import com.agentos.model.entity.Tool;
import com.agentos.service.McpServerService;
import com.agentos.service.ToolService;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 工具中心控制器
 * <p>
 * 提供 MCP 服务管理、工具查询和 Agent-工具绑定三个维度的 API。
 * MCP 服务管理：注册、列表、编辑、删除、同步工具
 * 工具查询：全局工具列表（支持按来源过滤）
 * Agent-工具绑定：为 Agent 绑定/解绑工具、查询已绑工具
 * </p>
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ToolCenterController {

    private final McpServerService mcpServerService;
    private final ToolService toolService;

    // ==================== MCP 服务管理 ====================

    /**
     * 注册 MCP 服务
     *
     * @param req 服务注册参数
     * @return 注册成功的 MCP 服务
     */
    @PostMapping("/mcp-servers")
    @SaCheckLogin
    public R<McpServer> createMcpServer(@Valid @RequestBody CreateMcpServerReq req) {
        return R.ok(mcpServerService.create(req));
    }

    /**
     * 分页查询 MCP 服务列表
     *
     * @param page 页码
     * @param size 每页大小
     * @return MCP 服务分页数据
     */
    @GetMapping("/mcp-servers")
    @SaCheckLogin
    public R<Page<McpServer>> listMcpServers(@RequestParam(defaultValue = "1") int page,
                                              @RequestParam(defaultValue = "10") int size) {
        return R.ok(mcpServerService.page(page, size));
    }

    /**
     * 更新 MCP 服务信息
     *
     * @param id  MCP 服务 ID
     * @param req 更新参数（仅非空字段生效）
     * @return 更新后的 MCP 服务
     */
    @PutMapping("/mcp-servers/{id}")
    @SaCheckLogin
    public R<McpServer> updateMcpServer(@PathVariable Long id, @RequestBody UpdateMcpServerReq req) {
        return R.ok(mcpServerService.update(id, req));
    }

    /**
     * 删除 MCP 服务
     * <p>
     * 级联删除该 MCP 服务器关联的所有工具及 Agent-工具绑定关系。
     * </p>
     *
     * @param id MCP 服务 ID
     * @return 无数据
     */
    @DeleteMapping("/mcp-servers/{id}")
    @SaCheckLogin
    public R<Void> deleteMcpServer(@PathVariable Long id) {
        mcpServerService.delete(id);
        return R.ok(null);
    }

    /**
     * 同步 MCP 服务的工具列表
     * <p>
     * 调用 Python Runtime 连接外部 MCP 服务器，拉取最新工具 Schema
     * 并同步到 tool 表中。同步过程中会计算 version_hash 避免无效更新。
     * </p>
     *
     * @param id MCP 服务 ID
     * @return 无数据
     */
    @PostMapping("/mcp-servers/{id}/sync")
    @SaCheckLogin
    public R<Void> syncMcpServer(@PathVariable Long id) {
        mcpServerService.sync(id);
        return R.ok(null);
    }

    // ==================== 工具查询 ====================

    /**
     * 分页查询全局工具列表
     *
     * @param page   页码
     * @param size   每页大小
     * @param source 来源过滤（builtin / mcp），可选
     * @return 工具分页数据
     */
    @GetMapping("/tools")
    @SaCheckLogin
    public R<Page<Tool>> listTools(@RequestParam(defaultValue = "1") int page,
                                   @RequestParam(defaultValue = "10") int size,
                                   @RequestParam(required = false) String source) {
        return R.ok(toolService.page(page, size, source));
    }

    // ==================== Agent-工具绑定 ====================

    /**
     * 为 Agent 绑定多个工具
     * <p>
     * 已绑定的工具会被自动跳过，保证操作幂等性。
     * 只有 MCP 工具需要显式绑定，内置工具默认可用。
     * </p>
     *
     * @param id  Agent ID
     * @param req 要绑定的工具 ID 列表
     * @return 无数据
     */
    @PostMapping("/agents/{id}/tools")
    @SaCheckLogin
    public R<Void> bindTools(@PathVariable Long id, @Valid @RequestBody BindToolsReq req) {
        toolService.bindTools(id, req.getToolIds());
        return R.ok(null);
    }

    /**
     * 查询 Agent 已绑定的工具列表
     *
     * @param id Agent ID
     * @return 工具列表
     */
    @GetMapping("/agents/{id}/tools")
    @SaCheckLogin
    public R<List<Tool>> listAgentTools(@PathVariable Long id) {
        return R.ok(toolService.listByAgent(id));
    }

    /**
     * 解绑 Agent 的某个工具
     *
     * @param id     Agent ID
     * @param toolId 工具 ID
     * @return 无数据
     */
    @DeleteMapping("/agents/{id}/tools/{toolId}")
    @SaCheckLogin
    public R<Void> unbindTool(@PathVariable Long id, @PathVariable Long toolId) {
        toolService.unbindTool(id, toolId);
        return R.ok(null);
    }
}
