package com.agentos.model.dto;

import lombok.Data;

// 登录响应
@Data
public class LoginResp {
    private String tokenName;
    private String tokenValue;
    private Long userId;
    private String username;
    private String displayName;
    private String avatarUrl;
}
