"""
SearchTool —— 网页搜索工具（内置工具）。

通过 HTTP GET 调用搜索 API 获取互联网信息。
V2 默认使用 DuckDuckGo 公开搜索 API（无需 API Key）。
可通过 SEARCH_API_URL 环境变量切换为其他搜索服务。
"""
import os
from typing import Any, Dict, Optional

import httpx

from tools.base import Tool


# ---------------------------------------------------------------------------
# SearchTool
# ---------------------------------------------------------------------------

class SearchTool(Tool):
    """
    网页搜索工具。

    通过配置的搜索 API 获取互联网信息。
    V2 默认使用 DuckDuckGo Lite API（无需认证，结果简洁）。
    生产环境建议切换为 Tavily / SerpAPI / Bing Search 等专业搜索服务。

    环境变量配置：
      SEARCH_API_URL：搜索 API 地址（默认：https://api.duckduckgo.com）
      SEARCH_API_KEY：搜索 API Key（DuckDuckGo 不需要）
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="web_search",
            description="搜索互联网获取最新信息。输入应为搜索关键词或问题。"
                        "当需要获取实时信息、最新新闻、或知识库之外的内容时使用。",
        )
        self.api_key = api_key or os.getenv("SEARCH_API_KEY", "")

    async def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行网页搜索。

        从 parameters 中获取查询词，支持以下键（按优先级）：
          - query
          - input
          - q

        Args:
            parameters: 工具参数字典，包含查询词

        Returns:
            搜索结果的文本摘要（前 2000 字符）
        """
        # 提取查询词（兼容多种参数名）
        query = (parameters.get("query")
                 or parameters.get("input")
                 or parameters.get("q")
                 or "")

        if not query.strip():
            return "错误：搜索关键词不能为空"

        return await self._search(query)

    async def _search(self, query: str) -> str:
        """
        实际搜索逻辑。

        Try 顺序：
          1. 自定义搜索 API（SEARCH_API_URL）
          2. DuckDuckGo Lite API（备选）
        """
        search_url = os.getenv("SEARCH_API_URL", "https://api.duckduckgo.com")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 尝试使用 DuckDuckGo Lite API（返回 JSON）
                resp = await client.get(
                    search_url,
                    params={"q": query, "format": "json", "no_html": "1"},
                    headers={"User-Agent": "AgentOS-Runtime/2.0"},
                )

                if resp.status_code == 200:
                    data = resp.json()
                    # DuckDuckGo 返回结构：AbstractText, RelatedTopics, ...
                    abstract = data.get("AbstractText", "")
                    if abstract:
                        return f"搜索结果（{query}）：\n{abstract[:2000]}"

                    # 尝试从 RelatedTopics 提取
                    topics = data.get("RelatedTopics", [])
                    if topics:
                        results = []
                        for t in topics[:5]:
                            if "Text" in t:
                                results.append(t["Text"])
                            elif "Topics" in t:
                                for sub in t["Topics"][:3]:
                                    if "Text" in sub:
                                        results.append(sub["Text"])
                        if results:
                            return f"搜索结果（{query}）：\n" + "\n".join(results[:5])

                    return f"未找到与 \"{query}\" 相关的搜索结果。"

                # 如果 DuckDuckGo 失败，尝试纯文本 HTML 版本
                resp2 = await client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params={"q": query},
                    headers={"User-Agent": "AgentOS-Runtime/2.0"},
                )
                if resp2.status_code == 200:
                    # 提取纯文本
                    text = resp2.text
                    import re
                    # 简单清理 HTML 标签
                    clean = re.sub(r'<[^>]+>', ' ', text)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    return clean[:2000] if clean else f"搜索 \"{query}\" 无结果。"

                return f"搜索服务暂时不可用（状态码: {resp.status_code}）"

        except httpx.TimeoutException:
            return f"搜索 \"{query}\" 超时，请稍后重试。"
        except Exception as e:
            return f"搜索失败: {e}"

    def to_openai_schema(self) -> Dict[str, Any]:
        """返回 OpenAI function calling 格式的 schema。"""
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词或自然语言问题，"
                                           "如 \"2025年诺贝尔奖得主\"",
                        },
                    },
                    "required": ["query"],
                },
            },
        }
