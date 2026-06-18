package com.agentos.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.agentos.common.BusinessException;
import com.agentos.mapper.UserApiKeyMapper;
import com.agentos.model.entity.UserApiKey;
import com.agentos.service.UserApiKeyService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserApiKeyServiceImpl implements UserApiKeyService {

    private final UserApiKeyMapper userApiKeyMapper;

    @Override
    public List<UserApiKey> list() {
        Long userId = StpUtil.getLoginIdAsLong();
        return userApiKeyMapper.selectList(
                new LambdaQueryWrapper<UserApiKey>()
                        .eq(UserApiKey::getUserId, userId)
        );
    }

    @Override
    public UserApiKey getById(Long id) {
        UserApiKey key = userApiKeyMapper.selectById(id);
        if (key == null) {
            throw new BusinessException("API Key 不存在");
        }
        if (!key.getUserId().equals(StpUtil.getLoginIdAsLong())) {
            throw new BusinessException("无权操作该 API Key");
        }
        return key;
    }

    @Override
    public UserApiKey getByUserAndProvider(Long userId, String provider) {
        return userApiKeyMapper.selectOne(
                new LambdaQueryWrapper<UserApiKey>()
                        .eq(UserApiKey::getUserId, userId)
                        .eq(UserApiKey::getProvider, provider)
                        .eq(UserApiKey::getIsActive, 1)
        );
    }

    @Override
    public UserApiKey save(UserApiKey userApiKey) {
        userApiKey.setId(null);
        userApiKey.setUserId(StpUtil.getLoginIdAsLong());
        if (userApiKey.getIsActive() == null) {
            userApiKey.setIsActive(1);
        }
        // 检查是否已存在相同 (user_id, provider)
        UserApiKey exist = getByUserAndProvider(userApiKey.getUserId(), userApiKey.getProvider());
        if (exist != null) {
            throw new BusinessException("该供应商的 API Key 已存在，请编辑或删除后重新添加");
        }
        userApiKeyMapper.insert(userApiKey);
        return userApiKeyMapper.selectById(userApiKey.getId());
    }

    @Override
    public UserApiKey update(UserApiKey userApiKey) {
        if (userApiKey.getId() == null) {
            throw new BusinessException("id 不能为空");
        }
        UserApiKey exist = userApiKeyMapper.selectById(userApiKey.getId());
        if (exist == null) {
            throw new BusinessException("API Key 不存在");
        }
        if (!exist.getUserId().equals(StpUtil.getLoginIdAsLong())) {
            throw new BusinessException("无权操作该 API Key");
        }
        userApiKey.setUserId(null);
        userApiKeyMapper.updateById(userApiKey);
        return userApiKeyMapper.selectById(userApiKey.getId());
    }

    @Override
    public void delete(Long id) {
        UserApiKey key = getById(id);
        userApiKeyMapper.deleteById(id);
    }
}
