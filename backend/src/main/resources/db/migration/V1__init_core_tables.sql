-- V1__init_core_tables.sql

-- 用户表（Spring Security 或者 so-token 所需）
CREATE TABLE sys_user (
                        id          BIGSERIAL    PRIMARY KEY,
                        username    VARCHAR(50)  NOT NULL UNIQUE,
                        password    VARCHAR(255) NOT NULL,            -- BCrypt 加密
                        display_name VARCHAR(100),
                        avatar_url  VARCHAR(255),
                        status      SMALLINT     DEFAULT 1,           -- 1:启用 0:禁用
                        created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                        updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 用户角色表（简化 RBAC）
CREATE TABLE sys_role (
                        id          BIGSERIAL    PRIMARY KEY,
                        name        VARCHAR(50)  NOT NULL UNIQUE,
                        description VARCHAR(255)
);

CREATE TABLE sys_user_role (
                            user_id     BIGINT NOT NULL REFERENCES sys_user(id),
                            role_id     BIGINT NOT NULL REFERENCES sys_role(id),
                            PRIMARY KEY (user_id, role_id)
);

-- Agent 定义表
CREATE TABLE agent (
                    id              BIGSERIAL    PRIMARY KEY,
                    name            VARCHAR(100) NOT NULL,
                    description     TEXT,
                    system_prompt   TEXT         NOT NULL,
                    model_provider  VARCHAR(20)  DEFAULT 'openai',  -- openai / gemini
                    model_name      VARCHAR(50)  DEFAULT 'gpt-4o-mini',
                    temperature     FLOAT        DEFAULT 0.7,
                    max_tokens      INT          DEFAULT 4096,
                    avatar_url      VARCHAR(255),
                    owner_id        BIGINT       REFERENCES sys_user(id),  -- 创建者
                    status          SMALLINT     DEFAULT 1,
                    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 对话/任务会话表
CREATE TABLE conversation (
                            id              BIGSERIAL    PRIMARY KEY,
                            title           VARCHAR(200),
                            user_id         BIGINT       NOT NULL REFERENCES sys_user(id),
                            agent_id        BIGINT       REFERENCES agent(id),
                            status          VARCHAR(20)  DEFAULT 'active',  -- active / completed / archived
                            created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                            updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 消息记录表（既是对话内容也是任务执行记录）
CREATE TABLE message (
                        id              BIGSERIAL    PRIMARY KEY,
                        conversation_id BIGINT       NOT NULL REFERENCES conversation(id),
                        role            VARCHAR(20)  NOT NULL,  -- user / assistant / system / tool
                        content         TEXT         NOT NULL,
                        metadata        JSONB,                  -- 额外信息（token 用量、工具调用等）
                        created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 任务日志表（观测用）
CREATE TABLE task_log (
                        id          BIGSERIAL    PRIMARY KEY,
                        task_id     VARCHAR(64),                 -- 关联 trace
                        agent_id    BIGINT       REFERENCES agent(id),
                        level       VARCHAR(10)  DEFAULT 'INFO',  -- INFO / WARN / ERROR
                        message     TEXT,
                        created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_conversation_user_id ON conversation(user_id);
CREATE INDEX idx_message_conversation_id ON message(conversation_id);
CREATE INDEX idx_task_log_task_id ON task_log(task_id);