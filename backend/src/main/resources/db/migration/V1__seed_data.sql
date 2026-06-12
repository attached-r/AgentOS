-- V1__seed_data.sql
INSERT INTO sys_role (name, description) VALUES
                                             ('ROLE_ADMIN', '系统管理员'),
                                             ('ROLE_USER', '普通用户');

-- 默认管理员 admin / admin123（密码需 BCrypt 编码后写入）
INSERT INTO sys_user (username, password, display_name) VALUES
    ('admin', '$2a$10$...', '管理员');

INSERT INTO sys_user_role (user_id, role_id) VALUES (1, 1);