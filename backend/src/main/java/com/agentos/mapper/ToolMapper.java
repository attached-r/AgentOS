package com.agentos.mapper;

import com.agentos.model.entity.Tool;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

/**
 * 工具数据访问接口
 */
@Mapper
public interface ToolMapper extends BaseMapper<Tool> {
}
