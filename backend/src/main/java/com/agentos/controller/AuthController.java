package com.agentos.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.agentos.common.R;
import com.agentos.model.dto.LoginReq;
import com.agentos.model.dto.LoginResp;
import com.agentos.model.dto.RegisterReq;
import com.agentos.service.UserService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth/")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;

    @PostMapping("login")
    public R<LoginResp> login(@Valid @RequestBody LoginReq req) {
        return R.ok(userService.login(req.getUsername(), req.getPassword()));
    }

    @PostMapping("register")
    public R<LoginResp> register(@Valid @RequestBody RegisterReq req) {
        return R.ok(userService.register(req));
    }

    @PostMapping("refresh")
    public R<LoginResp> refresh() {
        return R.ok(userService.refreshToken());
    }

    @PostMapping("logout")
    public R<Void> logout() {
        StpUtil.logout();
        return R.ok(null);
    }
}
