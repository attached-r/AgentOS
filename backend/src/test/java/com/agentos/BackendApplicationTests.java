package com.agentos;

import com.agentos.common.R;
import com.agentos.util.BCryptUtil;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class BackendApplicationTests {

    @Test
    void contextLoads() {
    }

    @Test
    void testR() {
        R<String> r = new R<>();
        r.setCode(200).setMsg("成功").setData("OK");
        System.out.println(r);
    }

    @Test
    void testBCrypt() {
        String password = "admin123";
        String hash = BCryptUtil.encode(password);
        System.out.println(hash);
    }
}
