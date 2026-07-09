package com.agentos.config;

import cn.dev33.satoken.interceptor.SaInterceptor;
import cn.dev33.satoken.stp.StpUtil;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class SecurityConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new SaInterceptor(handle -> StpUtil.checkLogin()))  // 指定拦截器采取sotoken拦截
                .addPathPatterns("/**")
                .excludePathPatterns(
                        "/api/auth/**",
                        "/api/agents/*/memories",
                        "/api/agents/*/memories/**",
                        "/api/knowledge/docs/search",
                        "/swagger-ui.html", "/swagger-ui/**",
                        "/v1/api-docs", "/v1/api-docs/**"
                );
    }
}
