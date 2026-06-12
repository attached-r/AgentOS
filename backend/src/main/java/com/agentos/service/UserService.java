package com.agentos.service;

import com.agentos.model.dto.LoginResp;
import com.agentos.model.dto.RegisterReq;
// 登录注册
public interface UserService {

    LoginResp login(String username, String password);

    LoginResp register(RegisterReq req);

    LoginResp refreshToken();
}
