#!/usr/bin/env python3
"""Verify that the published quickstart works with the supported MCP SDK."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from examples.quickstart import call_checked, describe_error, error_info


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
    print("PASS: quickstart SDK import and error handling")


if __name__ == "__main__":
    main()
