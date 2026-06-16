package com.agentos.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
public class RestTemplateConfig {
    // 创建 RestTemplate 实例
    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory(); // 连接工厂
        factory.setConnectTimeout(Duration.ofSeconds(5)); // 设置连接超时时间 5 秒
        factory.setReadTimeout(Duration.ofSeconds(60));   // 设置读取超时时间 60 秒

        return new RestTemplate(factory);
    }
}
