"""ADAMAS MCP 自建 agent 快速上手(官方 mcp SDK)。

运行:
    python -m pip install "mcp>=1.28.1,<2"
    ADAMAS_API_KEY=<your-api-key> python quickstart.py

演示推荐调用顺序:能力地图 → 产业景气度 → 已发布模型选股 → 最新信息流。
候选字段以实际端点为准；本例不提交付费研究，不自动重试工具。
API key 只从环境变量读取,绝不要写进代码。
"""
import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession
try:
    from mcp.client.streamable_http import streamable_http_client
except ImportError:
    from mcp.client.streamable_http import streamablehttp_client as streamable_http_client

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


def describe_error(result, payload):
    """Explain recovery without interpreting a delay as permission to replay."""
    failed, error, retry_after = error_info(result, payload)
    if not failed:
        return ""
    source = result.structuredContent
    if not isinstance(source, dict):
        source = payload if isinstance(payload, dict) else {}
    recovery = source.get("recovery")
    recovery = recovery if isinstance(recovery, dict) else {}
    parts = [str(error or "工具调用失败")]
    if source.get("error_class"):
        parts.append(f"类别={source['error_class']}")
    if recovery.get("action"):
        parts.append(f"处理={recovery['action']}")
    parts.append(f"可安全重放={recovery.get('retry_safe') is True}")
    if retry_after is not None:
        parts.append(f"等待建议={retry_after}秒")
    return "；".join(parts)


async def call_checked(session, name, arguments):
    result = await session.call_tool(name, arguments)
    payload = parse(result)
    if message := describe_error(result, payload):
        raise RuntimeError(f"{name}: {message}")
    return payload


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
            caps = await call_checked(session, "list_capabilities", {})
            print("数据新鲜度:", json.dumps(caps["freshness"], ensure_ascii=False))

            # 2) 产业景气度 + 模型选股
            ind = await call_checked(session, "get_industry_scores", {"industry": "存储"})
            top = ind["industries"][0]
            print(f"{top['name']} 景气度 {top['score']}(截至 {top.get('summary_as_of', '')[:10]})")
            picks = await call_checked(session, "get_model_picks", {"top_n": 3})
            for it in picks["picks"]:
                print(f"  模型第{it['rank']}名: {it['asset_name']} expected_return={it['expected_return']}")

            # 3) 最新信息流：文件日期不能当作每条事件发布日期。
            feed = await call_checked(session, "get_info_feed", {"limit": 3, "min_score": 5})
            if "items" in feed:
                print(f"\n最新文件要闻 {feed['count']} 条；as_of={feed.get('as_of')}，"
                      f"stale={feed.get('stale')}，availability={feed.get('availability')}")
                if "stale" not in feed:
                    print("当前端点尚未提供文件新鲜度，不能据此确认是今日要闻")
                elif feed.get("availability") == "not_generated":
                    print("文件尚未生成，空列表不代表市场没有新闻")
                elif feed.get("stale"):
                    print("文件已过期，请在引用中标明日期")
                for it in feed["items"]:
                    print(f"  [{it['score']}] {it['title']}")

            # 4) 检查错误与 recovery；本例只展示指引，不自动重放。
            bad_result = await session.call_tool(
                "get_company_tracking", {"company": "不存在的公司名xx"}
            )
            bad = parse(bad_result)
            if message := describe_error(bad_result, bad):
                print(f"\n(错误处理示例)服务端返回: {message}")


if __name__ == "__main__":
    asyncio.run(main())
