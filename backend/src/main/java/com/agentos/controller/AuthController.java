package com.agentos.controller;

import com.agentos.common.R;
import com.agentos.model.dto.LoginResp;
import com.agentos.model.dto.RegisterReq;
import com.agentos.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth/")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;

    @PostMapping("login")
    public R<LoginResp> login(String username, String password) {
        return R.ok(userService.login(username, password));
    }

    @PostMapping("register")
    public R<LoginResp> register(@RequestBody RegisterReq req) {
        return R.ok(userService.register(req));
    }

    @PostMapping("refresh")
    public R<LoginResp> refresh() {
        return R.ok(userService.refreshToken());
    }
}
