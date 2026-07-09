-- V2__rag_chunk.sql（在 V2__tool_and_memory.sql 之后执行）

-- ============================================================
-- RAG 文档分块存储
-- ============================================================

-- 知识库文档分块表：文档经 split_document() 分块后落此表
-- 检索时按块匹配内容而非整篇文档，提高命中精度
CREATE TABLE knowledge_chunk (
                                 id          BIGSERIAL    PRIMARY KEY,
                                 doc_id      BIGINT       NOT NULL REFERENCES knowledge_doc(id) ON DELETE CASCADE,
                                 content     TEXT         NOT NULL,
                                 seq         INT          DEFAULT 0,                 -- 块序号（文档内位置）
                                 title       VARCHAR(200),                            -- 所属文档标题（冗余，方便展示）
                                 created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 按文档 ID 快速查询（分页/删除文档时级联删除 chunk）
CREATE INDEX idx_knowledge_chunk_doc_id ON knowledge_chunk(doc_id);

-- 注意事项：
  -- ON DELETE CASCADE — 删除文档时自动删除所有对应 chunk
  -- seq 是块序号，对应 Chunk.index 字段（index 是 SQL 关键字，改用 seq）