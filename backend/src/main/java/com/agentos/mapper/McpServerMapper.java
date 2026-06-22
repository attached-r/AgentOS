package com.agentos.mapper;

import com.agentos.model.entity.McpServer;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

/**
 * MCP 服务数据访问接口
 */
@Mapper
public interface McpServerMapper extends BaseMapper<McpServer> {
}
