package com.agentos.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SpringDocConfig {

    @Bean
    public OpenAPI openAPI() {
        String tokenName = "agentos-token";

        return new OpenAPI()
                .info(new Info()
                        .title("AgentOS API")
                        .version("1.0.0")
                        .description("AgentOS 后端接口文档 — 基于 Sa-Token 认证"))
                // 全局安全方案：agentos-token header
                .addSecurityItem(new SecurityRequirement().addList(tokenName))
                .components(new Components()
                        .addSecuritySchemes(tokenName, new SecurityScheme()
                                .name(tokenName)
                                .type(SecurityScheme.Type.APIKEY)
                                .in(SecurityScheme.In.HEADER)
                                .description("登录后返回的 token 值"))
                );
    }
}
