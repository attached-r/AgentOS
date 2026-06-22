package com.agentos.mapper;

import com.agentos.model.entity.AgentTool;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

/**
 * Agent-工具关联数据访问接口
 */
@Mapper
public interface AgentToolMapper extends BaseMapper<AgentTool> {
}
