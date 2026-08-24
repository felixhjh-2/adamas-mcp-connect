"""Fail-closed static checks for the public Standard MCP contract."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STANDARD_TOOLS = {
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
    "submit_deep_research",
    "submit_stock_screen",
    "submit_notes_report",
    "get_research_task",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


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

    headings = set(re.findall(r"^#### `([^`]+)`", usage, re.MULTILINE))
    require(headings == STANDARD_TOOLS, f"工具清单漂移: {sorted(headings)}")
    readme_table = readme.split("## 能做什么", 1)[1].split("典型玩法", 1)[0]
    readme_tools = set(re.findall(r"`([a-z][a-z0-9_]+)`", readme_table))
    require(
        readme_tools == STANDARD_TOOLS,
        f"README 工具速览漂移: {sorted(readme_tools)}",
    )
    for document in (readme, usage):
        require("14 个工具" in document, "公开文档缺 Standard 14 工具口径")
        require("13" + " 个工具" not in document, "公开文档仍残留旧工具数口径")
    for document in (readme, usage, skill):
        for required in (
            "get_model_picks",
            "submit_stock_screen",
            "check_company_coverage",
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
    require("11 个 data 类 + 3 个 research 提交工具" in usage, "工具分类计数漂移")
    require("选股任务并发已满,请稍后重试" in usage, "选股并发错误文案漂移")
    require("CallToolResult.isError" in usage, "使用文档缺 isError 业务失败语义")
    require(
        "scratchpad/" + "prod_smoke.py" not in usage,
        "公开文档引用了不存在的生产脚本",
    )

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
    require(plugin["version"] == "2.2.0", "插件版本未升级到 2.2.0")
    require(marketplace["plugins"][0]["name"] == plugin["name"], "marketplace/plugin 名称漂移")
    require("adamas" in mcp["mcpServers"], "插件缺 adamas MCP 配置")
    print("PASS: public Standard contract is internally consistent")


if __name__ == "__main__":
    main()
