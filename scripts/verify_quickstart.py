#!/usr/bin/env python3
"""Verify that the published quickstart works with the supported MCP SDK."""

from __future__ import annotations

from types import SimpleNamespace

from examples.quickstart import error_info


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
    print("PASS: quickstart SDK import and error handling")


if __name__ == "__main__":
    main()
