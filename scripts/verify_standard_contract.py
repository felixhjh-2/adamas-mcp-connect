"""Fail-closed static checks for the public Standard MCP contract."""

from __future__ import annotations

import json
import re
import subprocess
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STANDARD_TOOL_ORDER = (
    "list_capabilities",
    "search_assets",
    "get_model_picks",
    "get_industry_scores",
    "get_company_tracking",
    "check_company_coverage",
    "get_industry_report",
    "get_industry_graph",
    "get_strategy_reports",
    "get_info_feed",
    "get_global_macro",
    "submit_deep_research",
    "submit_stock_screen",
    "submit_notes_report",
    "get_research_task",
)
STANDARD_TOOLS = set(STANDARD_TOOL_ORDER)
STANDARD_DATA_TOOLS = STANDARD_TOOLS - {
    "submit_deep_research",
    "submit_stock_screen",
    "submit_notes_report",
}
STANDARD_PROMPTS = {"industry_brief", "deep_research_report"}

# Hashes keep non-Standard capability names out of the public repository while still
# making every checked-in text artifact fail closed if one is accidentally published.
# This covers five higher-tier tool/prompt/metadata identifiers, six internal tool
# identifiers, and the internal tier label. The legal Standard research mode `pro`
# is deliberately not forbidden.
FORBIDDEN_PUBLIC_IDENTIFIER_DIGESTS = {
    "2125ebbc4985a7d986156c75da7c6317b9a741c3de95bc89f4433385b7aa10ff",
    "53bc99f84c3e122726e48034a269688f373a009e30d87f2bccdbc0fe850af132",
    "783b9c1f43a8b6a014ffa5f6a3318b61c9dd45314217673399ca7edc1fa3b5c7",
    "72bd81e15eac6b4fe13cb7dc417535ba367222f5d3b52b74177db6d11a7259af",
    "7900b7fd6b6e8630267054a58bda0654f0dc9c738eeba2856f41d750f336cf5b",
    "82f9baa3884ca4be6cfc6f493aa95da1579d1d16b2b658c4f1001806781873f5",
    "d039b38185cd0416ff3e361baf5094a7b27545139e4b146ca4578a86fb1d45bd",
    "29c7120b57d51db00540dafe21d360d842d68aabb97ad1c8d69a723718f4d5ad",
    "5b7f4c0b7ee3d9992fc000dfe7035d7312cb67a84fdc232401b5169f7b465daf",
    "0f41974be8adba6a6e653496d0a9d44e7883201f583016e746dc205360c4eb53",
    "356d78ad6e3b4a0eac17b63aeb3d8af2185500d5e44fc3f6df446dcbe67e126c",
    "9baf3a40312f39849f46dad1040f2f039f1cffa1238c41e9db675315cfad39b6",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def verify_public_boundary() -> None:
    leaks: list[str] = []
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\0")
    for relative_path in sorted(filter(None, tracked)):
        path = ROOT / relative_path
        try:
            lines = [relative_path, *path.read_text(encoding="utf-8").splitlines()]
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines):
            identifiers = re.findall(r"\b[a-z][a-z0-9_]{2,}\b", line.lower())
            if any(
                sha256(identifier.encode()).hexdigest()
                in FORBIDDEN_PUBLIC_IDENTIFIER_DIGESTS
                for identifier in identifiers
            ):
                leaks.append(f"{path.relative_to(ROOT)}:{line_number}")
    require(not leaks, f"公开材料含非 Standard 能力标识，位置: {leaks}")


def main() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    usage = (ROOT / "docs" / "USAGE.md").read_text(encoding="utf-8")
    skill = (
        ROOT
        / "plugins"
        / "adamas-research-report"
        / "skills"
        / "adamas-research-report"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    quickstart = (ROOT / "examples" / "quickstart.py").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    heading_rows = re.findall(r"^#### `([^`]+)`", usage, re.MULTILINE)
    headings = set(heading_rows)
    require(
        len(heading_rows) == len(STANDARD_TOOL_ORDER)
        and headings == STANDARD_TOOLS,
        f"工具精确白名单漂移: {heading_rows}",
    )
    require(
        tuple(heading_rows) == STANDARD_TOOL_ORDER,
        f"工具章节顺序漂移: {heading_rows}",
    )
    prompt_section = usage.split("### 7.1 MCP Prompts", 1)[1].split("### 7.2", 1)[0]
    prompt_rows = re.findall(
        r"^\| `([a-z][a-z0-9_]+)`",
        prompt_section,
        re.MULTILINE,
    )
    require(
        len(prompt_rows) == len(STANDARD_PROMPTS)
        and len(set(prompt_rows)) == len(prompt_rows)
        and set(prompt_rows) == STANDARD_PROMPTS,
        f"Prompt 清单漂移: {prompt_rows}",
    )
    readme_table = readme.split("## 能做什么", 1)[1].split("典型玩法", 1)[0]
    readme_tools = set(re.findall(r"`([a-z][a-z0-9_]+)`", readme_table))
    require(
        readme_tools == STANDARD_TOOLS,
        f"README 工具速览漂移: {sorted(readme_tools)}",
    )
    require(
        len(readme_tools) == len(STANDARD_TOOL_ORDER) == 15,
        f"Standard 工具计数漂移: README={len(readme_tools)} contract={len(STANDARD_TOOL_ORDER)}",
    )
    for document in (readme, usage):
        require("15 个工具" in document, "公开文档缺 Standard 15 工具口径")
        for stale_count in ("13", "14"):
            require(
                stale_count + " 个工具" not in document,
                f"公开文档仍残留旧工具数口径: {stale_count}",
            )
    for document in (readme, usage, skill):
        for required in (
            "get_model_picks",
            "submit_stock_screen",
            "check_company_coverage",
            "get_global_macro",
        ):
            require(required in document, f"公开材料缺 {required}")
    require("model_picks_as_of" in usage, "使用文档缺 model_picks_as_of")
    require("model_picks_as_of" in skill, "Skill 缺 model_picks_as_of")
    require(
        "get_model_picks(" + "asset_class_l1=对应行业)" not in skill,
        "Skill 仍把细分产业错误映射到 asset_class_l1",
    )
    require(
        skill.index("check_company_coverage") < skill.index("get_company_tracking"),
        "Skill 未保持 coverage-first 顺序",
    )
    for document in (readme, usage):
        for marker in ("自定义 Bearer 认证不能直接配置", "~/.codex/config.toml"):
            require(marker in document, f"公开接入口径缺 {marker}")
        require("${env:ADAMAS_API_KEY}" in document, "Cursor 配置未从环境变量读取 key")
        require('"type": "http"' not in document, "Cursor 配置仍携带多余 transport type")
    require(len(STANDARD_DATA_TOOLS) == 12, "data 类精确计数漂移")
    require("12 个 data 类 + 3 个 research 提交工具" in usage, "工具分类计数漂移")
    for document in (usage, skill):
        for marker in (
            "get_global_macro()",
            "China-Taiwan",
            "regions",
            "score_ready=false",
            "report_date",
            "disclaimer",
        ):
            require(marker in document, f"全球宏观公开契约缺 {marker}")
    for marker in (
        'get_global_macro(country="China")',
        'dimension="industry"',
        'report_date="2026-08-04"',
        '"country_name": "中国台湾地区"',
        "countries[].score",
        "regions[].score",
        "meta.disclaimer",
        "真实成功响应固定返回完整 9 项",
        "真实成功响应固定返回完整 9 格",
    ):
        require(marker in usage, f"全球宏观使用文档缺 {marker}")
    require(
        '"country_name": "中国台湾"' not in usage,
        "全球宏观地区示例不得使用旧展示名“中国台湾”",
    )
    require(
        usage.index("get_global_macro()")
        < usage.index('get_global_macro(country="China")')
        < usage.index('dimension="industry"'),
        "全球宏观调用顺序未保持 overview -> country -> report",
    )
    require("选股任务并发已满,请稍后重试" in usage, "选股并发错误文案漂移")
    require("CallToolResult.isError" in usage, "使用文档缺 isError 业务失败语义")
    sdk_requirement = "mcp>=1.28.1,<2"
    for document in (readme, usage, quickstart, workflow):
        require(sdk_requirement in document, f"公开材料缺已验证 SDK 版本 {sdk_requirement}")
    require(
        "python -m scripts.verify_quickstart" in workflow,
        "CI 未执行 quickstart SDK 与错误处理检查",
    )
    for marker in ("result.isError", 'structured.get("error")', "retry_after_seconds"):
        require(marker in quickstart, f"quickstart 错误处理缺 {marker}")
    require(
        "scratchpad/" + "prod_smoke.py" not in usage,
        "公开文档引用了不存在的生产脚本",
    )
    verify_public_boundary()

    plugin = json.loads(
        (
            ROOT
            / "plugins"
            / "adamas-research-report"
            / ".claude-plugin"
            / "plugin.json"
        ).read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    mcp = json.loads(
        (ROOT / "plugins" / "adamas-research-report" / ".mcp.json").read_text(
            encoding="utf-8"
        )
    )
    require(plugin["version"] == "2.3.0", "插件版本未升级到 2.3.0")
    for manifest_text in (plugin["description"], marketplace["plugins"][0]["description"]):
        require("15" in manifest_text, "插件清单缺 Standard 15 工具口径")
        require("全球宏观" in manifest_text, "插件清单缺全球宏观能力")
    require(marketplace["plugins"][0]["name"] == plugin["name"], "marketplace/plugin 名称漂移")
    require("adamas" in mcp["mcpServers"], "插件缺 adamas MCP 配置")
    print("PASS: public Standard contract is internally consistent")


if __name__ == "__main__":
    main()
