package com.agentos.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import com.agentos.common.R;
import com.agentos.model.entity.UserApiKey;
import com.agentos.service.UserApiKeyService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/user-api-keys")
@RequiredArgsConstructor
public class UserApiKeyController {

    private final UserApiKeyService userApiKeyService;

    /**
     * 获取当前用户的所有 API Key
     */
    @GetMapping
    @SaCheckLogin
    public R<List<UserApiKey>> list() {
        return R.ok(userApiKeyService.list());
    }

    /**
     * 获取单个 API Key
     */
    @GetMapping("/{id}")
    @SaCheckLogin
    public R<UserApiKey> getById(@PathVariable Long id) {
        return R.ok(userApiKeyService.getById(id));
    }

    /**
     * 新增 API Key
     */
    @PostMapping
    @SaCheckLogin
    public R<UserApiKey> save(@RequestBody UserApiKey userApiKey) {
        return R.ok(userApiKeyService.save(userApiKey));
    }

    /**
     * 更新 API Key
     */
    @PutMapping("/{id}")
    @SaCheckLogin
    public R<UserApiKey> update(@PathVariable Long id, @RequestBody UserApiKey userApiKey) {
        userApiKey.setId(id);
        return R.ok(userApiKeyService.update(userApiKey));
    }

    /**
     * 删除 API Key
     */
    @DeleteMapping("/{id}")
    @SaCheckLogin
    public R<Void> delete(@PathVariable Long id) {
        userApiKeyService.delete(id);
        return R.ok(null);
    }
}
