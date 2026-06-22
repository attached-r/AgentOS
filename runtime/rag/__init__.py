# runtime/rag — RAG（检索增强生成）管线
#
# V2 MVP 简化方案：
#   - 文档分块后通过后端 API 存入 PostgreSQL（不引入向量 DB）
#   - 检索时用关键词匹配（通过后端 ILIKE / tsvector 搜索）
#   - V3 才引入 Qdrant + fastembed 语义检索
#
# 流程：
#   1. Index: 文档分块 → 通过后端 API 存入 knowledge_doc 表
#   2. Retrieve: 用户查询 → 关键词匹配 → 返回 Top-K 片段
#   3. Generate: 将检索结果拼入 system prompt → LLM 生成
