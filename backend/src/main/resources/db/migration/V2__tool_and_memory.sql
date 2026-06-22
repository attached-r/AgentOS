-- V2__tool_and_memory.sql

-- ============================================================
-- 工具中心
-- ============================================================

-- MCP 服务注册表：每个 MCP 服务器对应一条记录
CREATE TABLE mcp_server (
                            id          BIGSERIAL    PRIMARY KEY,
                            name        VARCHAR(100) NOT NULL UNIQUE,
                            description VARCHAR(255),
                            endpoint    TEXT         NOT NULL,                -- TEXT 避免 URL 被截断
                            transport   VARCHAR(20)  DEFAULT 'sse',           -- sse / stdio
                            status      SMALLINT     DEFAULT 1,               -- 1:启用 0:禁用
                            created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                            updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 工具表：MCP 提供或 Runtime 内置的工具
CREATE TABLE tool (
                      id            BIGSERIAL    PRIMARY KEY,
                      mcp_server_id BIGINT       REFERENCES mcp_server(id) ON DELETE CASCADE,  -- NULL = 内置工具
                      name          VARCHAR(100) NOT NULL,
                      description   TEXT,
                      schema        JSONB,                                -- OpenAI function calling schema
                      source        VARCHAR(20)  DEFAULT 'builtin',        -- builtin / mcp
                      status        SMALLINT     DEFAULT 1,
                      version_hash  VARCHAR(64),                           -- schema 哈希，判断是否变更
                      created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                      synced_at     TIMESTAMP                              -- 最近一次从 MCP 同步的时间
);

-- Agent 与工具的关联表（只有 mcp 工具需要显式绑定）
CREATE TABLE agent_tool (
                            id          BIGSERIAL    PRIMARY KEY,
                            agent_id    BIGINT       NOT NULL REFERENCES agent(id) ON DELETE CASCADE,
                            tool_id     BIGINT       NOT NULL REFERENCES tool(id) ON DELETE CASCADE,
                            created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(agent_id, tool_id)
);

-- ============================================================
-- 记忆中心
-- ============================================================

-- 知识库文档（RAG 数据源）
CREATE TABLE knowledge_doc (
                               id               BIGSERIAL    PRIMARY KEY,
                               agent_id         BIGINT       REFERENCES agent(id) ON DELETE CASCADE,  -- NULL = 全局
                               title            VARCHAR(200),
                               content          TEXT         NOT NULL,
                               source           VARCHAR(50)  DEFAULT 'manual',       -- manual / upload / web
                               chunk_count      INT          DEFAULT 0,
                               embedding_status SMALLINT     DEFAULT 0,               -- 0:未索引 1:索引中 2:已索引
                               created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                               updated_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 记忆记录（长期记忆，从对话中提取的重要信息）
CREATE TABLE agent_memory (
                              id          BIGSERIAL    PRIMARY KEY,
                              agent_id    BIGINT       NOT NULL REFERENCES agent(id) ON DELETE CASCADE,
                              user_id     BIGINT       NOT NULL REFERENCES sys_user(id) ON DELETE CASCADE,
                              memory_type VARCHAR(20)  DEFAULT 'episodic',          -- working / episodic / semantic
                              content     TEXT         NOT NULL,
                              importance  FLOAT        DEFAULT 0.5,
                              metadata    JSONB,
                              created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 索引
-- ============================================================

CREATE INDEX idx_tool_mcp_server_id      ON tool(mcp_server_id);
CREATE INDEX idx_tool_source             ON tool(source);
CREATE INDEX idx_agent_tool_agent_id     ON agent_tool(agent_id);
CREATE INDEX idx_agent_tool_tool_id      ON agent_tool(tool_id);
CREATE INDEX idx_knowledge_doc_agent_id  ON knowledge_doc(agent_id);

-- agent_memory 常用查询的复合索引
CREATE INDEX idx_memory_lookup           ON agent_memory(agent_id, memory_type, importance DESC);
CREATE INDEX idx_memory_created          ON agent_memory(agent_id, created_at DESC);

---