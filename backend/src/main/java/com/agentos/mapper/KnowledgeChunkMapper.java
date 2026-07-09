package com.agentos.mapper;

import com.agentos.model.entity.KnowledgeChunk;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 知识库文档分块数据访问接口
 * <p>
 * CRUD 继承 MyBatis-Plus BaseMapper（含 insert/deleteById/selectById 等），
 * 另提供关键词搜索方法（PostgreSQL ILIKE 匹配）。
 * </p>
 */
@Mapper
public interface KnowledgeChunkMapper extends BaseMapper<KnowledgeChunk> {

    /**
     * 按关键词搜索 Chunk（ILIKE 匹配 content + title）
     *
     * @param keyword 搜索关键词
     * @param limit   返回上限
     * @return 匹配的 Chunk 列表（按块序号排序）
     */
    @Select("SELECT * FROM knowledge_chunk " +
            "WHERE content ILIKE '%' || #{keyword} || '%' " +
            "OR title ILIKE '%' || #{keyword} || '%' " +
            "ORDER BY seq " +
            "LIMIT #{limit}")
    List<KnowledgeChunk> searchByKeyword(@Param("keyword") String keyword,
                                         @Param("limit") int limit);

    /**
     * 按关键词 + 文档 ID 搜索 Chunk
     *
     * @param docId   文档 ID
     * @param keyword 搜索关键词
     * @param limit   返回上限
     * @return 匹配的 Chunk 列表
     */
    @Select("SELECT * FROM knowledge_chunk " +
            "WHERE doc_id = #{docId} " +
            "AND (content ILIKE '%' || #{keyword} || '%' " +
            "OR title ILIKE '%' || #{keyword} || '%') " +
            "ORDER BY seq " +
            "LIMIT #{limit}")
    List<KnowledgeChunk> searchByKeywordAndDoc(@Param("docId") Long docId,
                                                @Param("keyword") String keyword,
                                                @Param("limit") int limit);

    /**
     * 按文档 ID 删除所有 Chunk（级联删除兜底，某些场景需显式调用）
     *
     * @param docId 文档 ID
     */
    @Delete("DELETE FROM knowledge_chunk WHERE doc_id = #{docId}")
    void deleteByDocId(@Param("docId") Long docId);
}
