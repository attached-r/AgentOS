-- V2__user_api_key.sql
-- 用户 API Key 表
-- 每个用户可以为自己使用的每个供应商配置独立的 API Key
CREATE TABLE user_api_key (
    id          BIGSERIAL    PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES sys_user(id),
    provider    VARCHAR(20)  NOT NULL,              -- openai / gemini / deepseek 等
    api_key     VARCHAR(512) NOT NULL,              -- AES 加密存储（V2）
    base_url    VARCHAR(255),                       -- 可选：自定义 endpoint
    is_active   SMALLINT     DEFAULT 1,             -- 1:启用 0:停用
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, provider)                      -- 每个用户每供应商只能有一条
);

CREATE INDEX idx_user_api_key_user_id ON user_api_key(user_id);
