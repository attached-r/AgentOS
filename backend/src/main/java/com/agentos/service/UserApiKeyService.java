package com.agentos.service;

import com.agentos.model.entity.UserApiKey;

import java.util.List;

public interface UserApiKeyService {

    List<UserApiKey> list();

    UserApiKey getById(Long id);

    /**
     * 根据用户 ID 和供应商获取 API Key
     */
    UserApiKey getByUserAndProvider(Long userId, String provider);

    UserApiKey save(UserApiKey userApiKey);

    UserApiKey update(UserApiKey userApiKey);

    void delete(Long id);
}
