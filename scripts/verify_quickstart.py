#!/usr/bin/env python3
"""Verify that the published quickstart works with the supported MCP SDK."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from examples import quickstart
from examples.quickstart import call_checked, describe_error, error_info


def verify_nullable_summary_date() -> None:
    """Run the actual example to completion for valid nullable upstream dates."""
    expected = ["list_capabilities", "get_industry_scores", "get_model_picks",
                "get_info_feed", "get_company_tracking"]
    for summary_date in (None, "", "2026-10-12T08:00:00+08:00"):
        calls = []

        class Session:
            def __init__(self, *_):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                pass

            async def initialize(self):
                pass

            async def list_tools(self):
                return SimpleNamespace(tools=expected)

            async def call_tool(self, name, arguments):
                calls.append(name)
                payloads = {
                    "list_capabilities": {"freshness": {"company_reports_latest": "2026-10-12"}},
                    "get_industry_scores": {"industries": [{
                        "name": "存储", "sector": "tech", "score": 7.0,
                        "trends": {}, "summary_as_of": summary_date,
                    }], "count": 1, "disclaimer": "示例数据"},
                    "get_model_picks": {"picks": [{"rank": 1, "asset_name": "示例资产",
                                                   "expected_return": None}]},
                    "get_info_feed": {"items": [], "count": 0, "as_of": "2026-10-12",
                                      "stale": True, "availability": "available"},
                    "get_company_tracking": {"error": "未找到公司", "error_class": "NotFound"},
                }
                return SimpleNamespace(isError=name == "get_company_tracking",
                                       structuredContent=payloads[name])

        @asynccontextmanager
        async def http_client(**kwargs):
            assert kwargs["headers"] == {"Authorization": "Bearer offline-example-key"}
            yield object()

        @asynccontextmanager
        async def transport(*_, **__):
            yield object(), object(), None

        output = StringIO()
        with patch.dict(quickstart.os.environ, {"ADAMAS_API_KEY": "offline-example-key"}), \
                patch.object(quickstart.httpx, "AsyncClient", http_client), \
                patch.object(quickstart, "streamable_http_client", transport), \
                patch.object(quickstart, "ClientSession", Session), redirect_stdout(output):
            asyncio.run(quickstart.main())
        assert calls == expected, "nullable date must not interrupt or replay the example"
        text = output.getvalue()
        assert "模型第1名" in text and "错误处理示例" in text
        expected_date = "2026-10-12" if summary_date else "日期未提供"
        assert f"截至 {expected_date}" in text


def main() -> None:
    structured = SimpleNamespace(
        isError=True,
        structuredContent={"error": "structured", "retry_after_seconds": 11},
    )
    assert error_info(
        structured,
        {"error": "fallback", "retry_after_seconds": 7},
    ) == (True, "structured", 11)

    fallback = SimpleNamespace(isError=False, structuredContent=None)
    assert error_info(
        fallback,
        {"error": "fallback", "retry_after_seconds": 7},
    ) == (True, "fallback", 7)
    assert error_info(fallback, {}) == (False, None, None)

    receipt_unknown = SimpleNamespace(
        isError=True,
        structuredContent={
            "error": "结果未知", "error_class": "Upstream", "retry_after_seconds": 11,
            "recovery": {"action": "check_task_history", "retry_safe": False},
        },
    )
    description = describe_error(receipt_unknown, {})
    assert "check_task_history" in description
    assert "可安全重放=False" in description
    assert "等待建议=11秒" in description
    assert "后重试" not in description
    assert "可安全重放=False" in describe_error(fallback, {"error": "旧端点错误"})
    assert describe_error(fallback, {}) == ""

    class FailedSession:
        calls = 0

        async def call_tool(self, name, arguments):
            self.calls += 1
            return receipt_unknown

    session = FailedSession()
    try:
        asyncio.run(call_checked(session, "get_company_tracking", {}))
    except RuntimeError as error:
        assert "check_task_history" in str(error)
    else:
        raise AssertionError("business failure was accepted")
    assert session.calls == 1, "example must not automatically replay failures"
    verify_nullable_summary_date()
    print("PASS: quickstart SDK import and error handling")


if __name__ == "__main__":
    main()
