package com.agentos.mapper;

import com.agentos.model.entity.AgentMemory;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

/**
 * Agent 记忆数据访问接口
 */
@Mapper
public interface AgentMemoryMapper extends BaseMapper<AgentMemory> {
}
