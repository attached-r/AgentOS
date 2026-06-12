package com.agentos.service.impl;

import cn.dev33.satoken.stp.SaTokenInfo;
import cn.dev33.satoken.stp.StpUtil;
import com.agentos.common.BusinessException;
import com.agentos.util.BCryptUtil;
import com.agentos.mapper.SysUserMapper;
import com.agentos.model.dto.LoginResp;
import com.agentos.model.dto.RegisterReq;
import com.agentos.model.entity.SysUser;
import com.agentos.service.UserService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final SysUserMapper sysUserMapper;

    @Override
    public LoginResp login(String username, String password) {
        // 1.检查用户名密码
        SysUser user = sysUserMapper.selectOne(
                new LambdaQueryWrapper<SysUser>()
                        .eq(SysUser::getUsername, username)
        );
        // 2. 如果账号不存在或者密码错误 则返回错误
        if (user == null || !BCryptUtil.matches(password, user.getPassword())) {
            throw new BusinessException("用户名或密码错误");
        }
        if (user.getStatus() == null || user.getStatus() != 1) {
            throw new BusinessException("账号已被禁用");
        }
        // 3. 登录成功 将用户信息保存到 session/token 中
        StpUtil.login(user.getId());
        return buildLoginResp(user);
    }

    @Override
    public LoginResp register(RegisterReq req) {
        // 1. 检查用户名是否已存在
        Long count = sysUserMapper.selectCount(
                new LambdaQueryWrapper<SysUser>()
                        .eq(SysUser::getUsername, req.getUsername())
        );
        if (count != null && count > 0) {
            throw new BusinessException("用户名已被占用");
        }

        // 2.创建用户
        SysUser user = new SysUser();
        user.setUsername(req.getUsername());
        user.setPassword(BCryptUtil.encode(req.getPassword()));
        user.setDisplayName(req.getDisplayName());
        user.setStatus(1);
        sysUserMapper.insert(user);

        // 3.注册后自动登录
        StpUtil.login(user.getId());
        return buildLoginResp(user);
    }

    @Override
    public LoginResp refreshToken() {
        StpUtil.checkLogin();
        Long userId = StpUtil.getLoginIdAsLong();
        SysUser user = sysUserMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException("用户不存在");
        }
        // 重新登录生成新 token
        StpUtil.login(user.getId());
        return buildLoginResp(user);
    }
    // 构建登录响应
    private LoginResp buildLoginResp(SysUser user) {
        // 1. 获取 token 信息
        SaTokenInfo tokenInfo = StpUtil.getTokenInfo();
        // 2. 构建登录响应
        LoginResp resp = new LoginResp();
        resp.setTokenName(tokenInfo.getTokenName());
        resp.setTokenValue(tokenInfo.getTokenValue());
        resp.setUserId(user.getId());
        resp.setUsername(user.getUsername());
        resp.setDisplayName(user.getDisplayName());
        resp.setAvatarUrl(user.getAvatarUrl());
        return resp;
    }
}
