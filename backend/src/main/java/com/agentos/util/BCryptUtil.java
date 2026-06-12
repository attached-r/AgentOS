package com.agentos.util;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

/**
 * 密码加密 / 校验工具
 */
public class BCryptUtil {
    // 不加盐 加密
    public static String encode(String rawPassword) {
        // 采用BCryptPasswordEncoder
        return new BCryptPasswordEncoder().encode(rawPassword); // 已经内置加盐
    }
    // 校验 密码
    public static boolean matches(String rawPassword, String encodedPassword) {
        return new BCryptPasswordEncoder().matches(rawPassword, encodedPassword);
    }


}
