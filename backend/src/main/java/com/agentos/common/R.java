package com.agentos.common;

import lombok.Data;
import lombok.experimental.Accessors;

// R.java — 统一响应
@Data
@Accessors(chain = true)          // 支持链式调用
public class R<T> {
    private int code;        // 200 成功，非 200 失败
    private String msg;
    private T data;

    public static <T> R<T> ok(T data) {
        return new R<T>().setCode(200).setMsg("success").setData(data);
    }
    public static <T> R<T> fail(int code, String msg) {
        return new R<T>().setCode(code).setMsg(msg);
    }
}