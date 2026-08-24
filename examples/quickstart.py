"""ADAMAS MCP 自建 agent 快速上手(官方 mcp SDK)。

运行:
    python -m pip install "mcp>=1.28.1,<2"
    ADAMAS_API_KEY=<your-api-key> python quickstart.py

演示推荐调用顺序:能力地图 → 产业景气度 → 已发布模型选股 → 当日信息流。
API key 只从环境变量读取,绝不要写进代码。
"""
import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "https://www.adamas-research.com/mcp"


def parse(result):
    """优先 structured output;老版本 SDK 回退解析 JSON 文本,两种形态内容等价。"""
    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(result.content[0].text)


def error_info(result, payload):
    """同时读取 MCP 错误标记与结构化业务错误/退避时间。"""
    structured = result.structuredContent
    error = structured.get("error") if isinstance(structured, dict) else None
    retry_after = (
        structured.get("retry_after_seconds")
        if isinstance(structured, dict)
        else None
    )
    if error is None and isinstance(payload, dict):
        error = payload.get("error")
    if retry_after is None and isinstance(payload, dict):
        retry_after = payload.get("retry_after_seconds")
    return bool(result.isError or error), error, retry_after


async def main() -> None:
    api_key = os.environ.get("ADAMAS_API_KEY", "")
    if not api_key:
        sys.exit("请先设置环境变量 ADAMAS_API_KEY(向 ADAMAS 团队申请)")

    async with (
        httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as http_client,
        streamable_http_client(
            URL, http_client=http_client
        ) as (read, write, _),
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print(f"已连接,{len(tools.tools)} 个工具可用\n")

            # 1) 第一站:能力地图与数据新鲜度
            caps = parse(await session.call_tool("list_capabilities", {}))
            print("数据新鲜度:", json.dumps(caps["freshness"], ensure_ascii=False))

            # 2) 产业景气度 + 模型选股
            ind = parse(await session.call_tool("get_industry_scores", {"industry": "存储"}))
            top = ind["industries"][0]
            print(f"{top['name']} 景气度 {top['score']}(截至 {top.get('summary_as_of', '')[:10]})")
            picks = parse(await session.call_tool("get_model_picks", {"top_n": 3}))
            for it in picks["picks"]:
                print(f"  模型第{it['rank']}名: {it['asset_name']} 预期收益 {it['expected_return']:.1%}")

            # 3) 当日高分信息流
            feed = parse(await session.call_tool("get_info_feed", {"limit": 3, "min_score": 8}))
            if "items" in feed:
                print(f"\n今日高分要闻 {feed['count']} 条:")
                for it in feed["items"]:
                    print(f"  [{it['score']}] {it['title']}")

            # 4) 业务层错误的正确处理方式:检查返回里的 error / retry_after_seconds
            bad_result = await session.call_tool(
                "get_company_tracking", {"company": "不存在的公司名xx"}
            )
            bad = parse(bad_result)
            failed, error, retry_after = error_info(bad_result, bad)
            if failed:
                suffix = f"，{retry_after} 秒后重试" if retry_after is not None else ""
                print(f"\n(错误处理示例)服务端返回: {error or '工具调用失败'}{suffix}")


if __name__ == "__main__":
    asyncio.run(main())
