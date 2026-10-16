"""Fail-closed static checks for the public Standard MCP contract."""

from __future__ import annotations

import ipaddress
import json
import re
import subprocess
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STANDARD_TOOL_ORDER = (
    "list_capabilities",
    "get_my_quota",
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
    "submit_company_roundtable",
    "submit_kb_question",
    "regenerate_kb_answer",
    "get_research_task",
    "list_my_research_tasks",
    "list_kb_conversations",
    "get_kb_conversation",
    "delete_kb_conversation",
    "update_kb_message",
    "share_kb_content",
    "manage_kb_shares",
    "stop_kb_generation",
    "get_hot_notes",
)
STANDARD_TOOLS = set(STANDARD_TOOL_ORDER)
STANDARD_DATA_TOOLS = STANDARD_TOOLS - {
    "submit_deep_research",
    "submit_stock_screen",
    "submit_notes_report",
    "submit_company_roundtable",
    "submit_kb_question",
    "regenerate_kb_answer",
}
STANDARD_PROMPTS = {"industry_brief", "deep_research_report"}

# Hashes keep non-Standard capability names out of the public repository while still
# making every checked-in text artifact fail closed if one is accidentally published.
# The allowlist describes only Standard. Digests also cover restricted schema
# fields and additional capability identifiers. The legal research mode `pro`
# is deliberately not forbidden.
FORBIDDEN_PUBLIC_IDENTIFIER_DIGESTS = {
    "08c0a549884dfb16749c4fdc644245f1ed9a5d5d8d05168ecf423dffecc0e957",
    "14b48da5dd28a9193e03d326c78f23540a370c54be063ee47dc5cf88e9033ccd",
    "512064869cfefb9c2ff43c963b8370ccc29f5c85fb8a460166cb9d7f9a995641",
    "6cb7d485adc230fd05d7003b36ab67711839e5599133fb865db5e0db409ce80e",
    "7e4c390df13448f18ccbfba7e39335ead4915f4115243688d3e123cbba4d53b5",
    "a4041b96f7cd624a07626d797a9bd18be2739c49fb72d014742da7eaa616512b",
    "d5553786a713dc134d1db611ba7b5cdbf5c98d12e04646f22d9baacab44f34be",
    "f34d5ec4cdb2573310d17332b67e19653356136686482decfccfac9bea5e9b8f",
    "af03096fed90ed61efaf370e89686a258eea1d733ad749e0a07c00b469180312",
    "50ead54a10ff10018d57d5397928b40ded409a88a59dc0b8402d2dd863b08cd9",
    "ba9e3f0716bd6175bf57c5badd5c432c9c6cf00b32f88de965df37c9ff124a11",
    "c11b9df57a3f729a8cbd014bfb5a0eb0bd70695d66be1886442d5960daad8742",
    "cb56f5b5d2b36cef24ba302b65e5e25ba1d6499bd7c6e6874eb8caf78c635d56",
    "59df56f6428a076c95490334027477c4b02002e7a88b9b5011c8b3785933068e",
    "433681e87baea3dd50e239a14d5445cbf0a769ec1b50cf0c0f6be3211cffa4b1",
    "fd6b6dc73b6183a036d01ffec2ff682165e4382eb1028b71b59985359e68fcf7",
    "ec2cf9bad77d338f9e34a02d03da4616e969c86cf379dfc40caa5cd039bc31a3",
    "0433e36a960aad6513999c804ce78855a3d6791ae5682cf2f00c2558dfda2c28",
    "c1f90d105c9930d0594c2a935561eb75643692762042ec9e8c2c8b9037e192d2",
    "c1783b8c2a730b5aadf6d4f13a69dcd03b2d8d3521d270798b463ecd4f74e1c6",
    "06b82b3ad9993fb329bd227f2e79b0e666183949413f36d5bf8c6991428b78a0",
    "edbb743748408f8696ccb49f7c764c166c3e2d4543905e65bd661c7984073a77",
    "8ded575293aed0cf0adc8bb4d2f6432446e41a2ee0fb5d275b4759b7550d5b5d",
    "b6e934b7342e0cb822e0556240689957d14bdbd74b156c80d7d5afcc66173321",
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


# Generic credential/contact/path checks avoid embedding any real secret or host.
# These token grammars are ASCII; adjacent Chinese prose must be a boundary.
PUBLIC_CONTENT_PATTERNS = (
    re.compile("内" + "部" + "|" + "组" + "合" + "|" + "长" + "周期" + "方向"),
    re.compile(r"\badamas_[A-Za-z0-9_-]{24,}\b", re.ASCII),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", re.ASCII),
    re.compile(r"\b[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", re.ASCII),
    re.compile(r"/" + r"Users/[^\s`]+"),
    re.compile(r"(?:postgres(?:ql)?|mysql|redis)://[^\s`]+", re.I),
)
IPV4_LITERAL = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])", re.ASCII)


def content_leaks(line: str) -> bool:
    if any(pattern.search(line) for pattern in PUBLIC_CONTENT_PATTERNS):
        return True
    for literal in IPV4_LITERAL.findall(line):
        try:
            address = ipaddress.ip_address(literal)
        except ValueError:
            continue
        # Client callback examples may use loopback; service IPs are not public docs.
        if not address.is_loopback:
            return True
    return False


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def verify_kb_versions_documentation(documents: tuple[str, ...]) -> None:
    # These are simultaneous limits: a valid item/serialized field can still
    # exceed the independent UTF-8 transport limit. Never publish a per-item
    # 400000 allowance alongside a correct aggregate paragraph elsewhere.
    incorrect_item_limit = re.compile(r"(?:每项|单项)\s*(?:最多|不超过|上限为|为|[≤<]=?)?\s*[`*]*400000")
    for document in documents:
        require(not incorrect_item_limit.search(document), "versions 错写每项400000字符")
        for marker in ("changes.versions", "最多20项", "每项≤399996个Unicode字符",
                       "完整数组", "json.dumps(versions, ensure_ascii=False)",
                       "默认格式序列化后≤400000个Unicode字符", "含括号、引号、转义、逗号和空格",
                       "非ASCII字符不转义", "元素之间用逗号加一个空格分隔",
                       "仍须满足完整 UTF-8 JSON-RPC 请求体的 1 MiB 上限"):
            require(marker in document, f"versions 序列化与完整请求限制说明缺 {marker}")


def verify_boundary_self_checks() -> None:
    from types import SimpleNamespace
    from unittest.mock import patch

    probes = (
        "内" + "部", "组" + "合", "长" + "周期" + "方向",
        "probe" + "@" + "example.invalid",
        "/" + "Users/placeholder/private",
        "postgresql" + "://placeholder@invalid/qa",
        "203" + "." + "0.113.42",
        "adamas_" + "x" * 32,
    )
    for index, probe in enumerate(probes):
        require(content_leaks(probe), f"公开边界负例未被拒绝: {index}")
    require(not content_leaks("http://127.0.0.1:9200/mcp"), "误拦客户端 loopback")
    require(not content_leaks("probe@users.noreply.github.com"), "误拦 GitHub noreply")

    contexts = (("", ""), ("中文", ""), ("", "中文"), ("前文", "后文"),
                ("（", "），"), ("prefix=", "; suffix"))
    api_key = "adamas_" + "x" * 32
    aws_ids = ("AKIA" + "A" * 16, "ASIA" + "B" * 16)
    email = "probe" + "@" + "example.invalid"
    public_ip = "203" + ".0.113.42"
    for token_index, token in enumerate((api_key, *aws_ids, email, public_ip)):
        for context_index, (left, right) in enumerate(contexts):
            require(content_leaks(left + token + right),
                    f"ASCII 敏感 token 邻接漏检: {token_index}/{context_index}")
    for allowed in ("http://127.0.0.1:9200/mcp", "probe" + "@" + "users.noreply.github.com"):
        for left, right in contexts:
            require(not content_leaks(left + allowed + right), "误拦允许 token 邻接")

    non_tokens = (
        "x" + api_key, "_" + api_key, "adamas_" + "x" * 23,
        *(prefix + token for token in aws_ids for prefix in ("x", "0", "_")),
        *(token + suffix for token in aws_ids for suffix in ("x", "0", "_")),
        "AKIA" + "A" * 15, "ASIA" + "B" * 17,
        email + "9", email + "_", "probe" + "@" + "localhost",
        *(prefix + public_ip for prefix in ("x", "_", "1.")),
        *(public_ip + suffix for suffix in ("x", "_", ".1")),
        "999" + ".0.113.42",
    )
    for index, token in enumerate(non_tokens):
        require(not content_leaks(token), f"误把 ASCII 非 token 当成敏感值: {index}")
    # A legal suffix extends these variable-length tokens instead of invalidating them.
    require(content_leaks(api_key + "x_"), "漏检带合法后缀的 API token")
    require(content_leaks("x" + email), "漏检扩展本地名的邮件 token")

    # Exercise the actual tracked-file scanner with a synthetic digest, never a private name.
    identifier = "synthetic_boundary_identifier"
    def scanner_rejects_identifier(line: str) -> bool:
        with (
            patch.dict(globals(), FORBIDDEN_PUBLIC_IDENTIFIER_DIGESTS={sha256(identifier.encode()).hexdigest()}),
            patch.object(subprocess, "run", return_value=SimpleNamespace(stdout="boundary-probe.md\0")),
            patch.object(Path, "read_text", return_value=line),
        ):
            try:
                verify_public_boundary()
            except SystemExit:
                return True
        return False

    for left, right in contexts:
        require(scanner_rejects_identifier(left + identifier + right), "受限 ASCII 标识邻接漏检")
    for token in ("x" + identifier, "_" + identifier, identifier + "x", identifier + "_"):
        require(not scanner_rejects_identifier(token), "误拦扩展 ASCII 标识")


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
            identifiers = re.findall(r"\b[a-z][a-z0-9_]{2,}\b", line.lower(), re.ASCII)
            if any(
                sha256(identifier.encode()).hexdigest()
                in FORBIDDEN_PUBLIC_IDENTIFIER_DIGESTS
                for identifier in identifiers
            ) or content_leaks(line):
                leaks.append(f"{path.relative_to(ROOT)}:{line_number}")
    require(not leaks, f"公开材料含受限标识或敏感内容，位置: {leaks}")


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
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

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
        len(readme_tools) == len(STANDARD_TOOL_ORDER) == 28,
        f"Standard 工具计数漂移: README={len(readme_tools)} contract={len(STANDARD_TOOL_ORDER)}",
    )
    for document in (readme, usage):
        require("28 个工具" in document, "公开文档缺 Standard 28 工具口径")
        counts = re.findall(r"(?<!\d)(\d+)\s*个(?:对外|投研)?工具", document)
        require(bool(counts) and set(counts) == {"28"}, f"公开文档工具数不一致: {counts}")
        for stale_count in ("13", "14", "15", "17"):
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
    require("最新已发布的量化选股" in skill, "Skill 缺量化选股明确口径")
    for stale_model_wording in (
        "最新模型选股排名",
        "取已发布排名",
        "已发布模型排名参考",
        "补最新模型偏好",
    ):
        require(stale_model_wording not in skill, f"Skill 残留模糊选股文案: {stale_model_wording}")
    oauth_sections = (
        readme.split("### ChatGPT / Claude / 其他 MCP 客户端", 1)[1].split(
            "### 自建 agent", 1
        )[0],
        usage.split("### 2.6 ChatGPT / Claude / 其他 MCP 客户端", 1)[1].split(
            "### 2.7 自建 agent", 1
        )[0],
    )
    claude_code_sections = (
        readme.split("### Claude Code", 1)[1].split("### Codex", 1)[0],
        usage.split("### 2.3 Claude Code", 1)[1].split("### 2.4 Codex", 1)[0],
    )
    claude_oauth_command = (
        "claude mcp add --transport http adamas "
        "https://www.adamas-research.com/mcp"
    )
    for section in claude_code_sections:
        for marker in (
            "OAuth",
            claude_oauth_command,
            "claude mcp login adamas",
            "/mcp",
            "https://code.claude.com/docs/en/mcp",
            "Bearer key",
            "ADAMAS_API_KEY",
        ):
            require(marker in section, f"Claude Code 接入章节缺 {marker}")
        require(
            section.index(claude_oauth_command) < section.index("Authorization: Bearer"),
            "Claude Code 接入未把 OAuth 无请求头方案放在 Bearer 方案之前",
        )
    callback_hosts = (
        "chatgpt.com",
        "claude.ai",
        "claude.com",
        "www.cursor.com",
        "vscode.dev",
        "insiders.vscode.dev",
        "localhost",
        "127.0.0.1",
        "::1",
    )
    for document, oauth_section in zip((readme, usage), oauth_sections, strict=True):
        for marker in ("OAuth 自动授权", "~/.codex/config.toml"):
            require(marker in document, f"公开接入口径缺 {marker}")
        for marker in callback_hosts:
            require(marker in oauth_section, f"OAuth 章节回调白名单缺 {marker}")
        require(
            "无需手工填 key 或 client secret" in oauth_section,
            "OAuth public client 章节未明确无需 client secret",
        )
        require("${env:ADAMAS_API_KEY}" in document, "Cursor 配置未从环境变量读取 key")
        require('"type": "http"' not in document, "Cursor 配置仍携带多余 transport type")
    for marker in ("token_endpoint_auth_method=none", "S256 PKCE", "无需 `client_secret`"):
        require(marker in oauth_sections[1], f"OAuth public client 章节契约缺 {marker}")
    for oauth_section in oauth_sections:
        for marker in (
            "https://developers.openai.com/plugins/deploy/connect-chatgpt",
            "https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt-beta",
            "Business",
            "Enterprise",
            "Edu",
            "Pro",
            "read/fetch",
            "ChatGPT Web",
            "token_endpoint_auth_method=none",
            "S256 PKCE",
            "refresh token",
        ):
            require(marker in oauth_section, f"ChatGPT / OAuth 接入章节缺 {marker}")
    kimi_sections = (
        readme.split("### Kimi Code", 1)[1].split("### Claude Code", 1)[0],
        usage.split("### 2.2 Kimi Code", 1)[1].split("### 2.3 Claude Code", 1)[0],
    )
    expected_kimi_config = {
        "mcpServers": {
            "adamas": {
                "url": "https://www.adamas-research.com/mcp",
                "bearerTokenEnvVar": "ADAMAS_API_KEY",
            }
        }
    }
    for section in kimi_sections:
        for marker in (
            "~/.kimi-code/mcp.json",
            "ADAMAS_API_KEY",
            "/mcp",
            "https://www.kimi.com/code/docs/kimi-code-cli/customization/mcp.html",
            "Kimi Code for VS Code",
            "KIMI_CODE_HOME",
            "共享",
            "https://www.kimi.com/code/docs/kimi-code-for-vscode/customization.html",
            "https://github.com/MoonshotAI/kimi-code/tree/main/apps/vscode",
            "不要带 `Bearer ` 前缀",
        ):
            require(marker in section, f"Kimi Code 接入口径缺 {marker}")
        match = re.search(r"```json\n(\{.*?\})\n```", section, re.DOTALL)
        require(match is not None, "Kimi Code 接入缺 JSON 配置示例")
        require(
            json.loads(match.group(1)) == expected_kimi_config,
            "Kimi Code MCP 配置漂移",
        )
    kimi_skill_sections = (
        readme.split("## 安装 Skill", 1)[1].split("## 申请 API key", 1)[0],
        usage.split("### 7.2 WorkBuddy / OpenClaw / Kimi Code Skill 包", 1)[1].split(
            "## 8. FAQ", 1
        )[0],
    )
    for section in kimi_skill_sections:
        require("/skill:adamas-research-report" in section, "Kimi Code Skill 调用说明缺失")
        require(
            ".kimi-code/skills/adamas-research-report/" in section,
            "Kimi Code Skill 安装路径缺失",
        )
    require(len(STANDARD_DATA_TOOLS) == 22, "data 类精确计数漂移")
    require("22 个 data 类入口 + 6 个 research 提交工具" in usage, "工具分类计数漂移")
    for document in (usage, skill):
        for marker in (
            "get_global_macro()",
            "China-Taiwan",
            "regions",
            "score_ready=false",
            "disclaimer",
        ):
            require(marker in document, f"全球宏观公开契约缺 {marker}")
    macro_usage = usage.split("#### `get_global_macro`", 1)[1].split("\n---", 1)[0]
    require("每个经济体×维度只提供最新版" in macro_usage,
            "全球宏观文档缺最新版唯一口径")
    require("当前工具 schema 暂保留 `report_date`" in macro_usage,
            "全球宏观文档缺滚动兼容参数说明")
    require("每个经济体×维度只提供最新报告" in skill,
            "Skill 缺全球宏观最新版唯一口径")
    for removed in (
        "| `report_date` |",
        "`dates`",
        "dates[]",
        "`periods`",
        "periods}",
        "历史期",
    ):
        require(removed not in macro_usage, f"全球宏观仍暴露历史契约: {removed}")
    macro_skill_method = skill.split(
        "2.6 **全球宏观先拉全景,再读正文**", 1
    )[1].split("3. **数据与观点分开取、分开写**", 1)[0]
    macro_skill_playbook = skill.split("**全球宏观对比**", 1)[1].split(
        "**产业链量化选股**", 1
    )[0]
    for removed in ("`dates`", "`periods`", "report_date=", "历史日期"):
        require(
            removed not in macro_skill_method and removed not in macro_skill_playbook,
            f"Skill 全球宏观仍引导历史调用: {removed}",
        )
    for marker in (
        'get_global_macro(country="China")',
        'dimension="industry"',
        '"report_date": "2026-08-04"',
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
    for document in (readme, usage, skill):
        for marker in ("2.6.3", "接入材料", "get_my_quota", "list_my_research_tasks",
                       "recovery", "retry_safe", "content_status", "stale", "doc_id_mapping"):
            require(marker in document, f"正式契约缺 {marker}")
        for stale in ("候选契约", "候选版本", "尚未发布", "本候选"):
            require(stale not in document, f"当前文档仍标为未正式发布: {stale}")
        for marker in ("POST /mcp", "UTF-8 JSON-RPC", "1 MiB（1048576 bytes）", "list_capabilities().transport.request_limits",
                       "字段字符上限不等于完整请求字节上限", "中文、emoji、JSON 转义", "HTTP 413",
                       "本次请求未进入工具业务", "不能据此推断此前受理状态未知的提交未被受理",
                       "不自动截断文本、丢弃 history 或 versions", "不换键重投写入或收费操作", "网页编辑",
                       "用户明确缩小输入范围"):
            require(marker in document, f"公开完整请求大小或安全恢复说明缺 {marker}")
    verify_kb_versions_documentation((readme, usage, skill))
    for marker in ("next_cursor", "has_more", "file_mtime", "source_updated_at",
                   "matched_node_ids", "context_node_ids", "ambiguous", "citation_note",
                   "download_links_status", "idempotency_persisted", "task_status",
                   "[A-Za-z0-9][A-Za-z0-9_.:-]*", "新键不等于恢复原任务"):
        require(marker in usage, f"正式使用文档缺 {marker}")
    for tool in ("submit_deep_research", "submit_stock_screen", "submit_notes_report", "submit_company_roundtable", "submit_kb_question", "regenerate_kb_answer"):
        section = usage.split(f"#### `{tool}`", 1)[1].split("\n#### `", 1)[0]
        require("| `idem_key` | string | 否 | 空串 |" in section,
                f"付费提交缺可选幂等参数: {tool}")
    for document in (readme, skill):
        for marker in ("idem_key", "idempotency_persisted", "session_id", "BadParam"):
            require(marker in document, f"正式付费恢复说明缺 {marker}")
    for document in (readme, usage, skill):
        for marker in ("submit_company_roundtable", "get_hot_notes", "list_kb_conversations",
                       "get_kb_conversation", "delete_kb_conversation", "update_kb_message",
                       "share_kb_content", "manage_kb_shares", "stop_kb_generation",
                       "not_cancellable_here"):
            require(marker in document, f"新增 Standard 能力或停止边界缺 {marker}")
    require("六个付费提交工具" in skill, "Skill 付费提交数量漂移")
    require("data 类不等于只读" in usage, "网页写操作未说明配额分类和副作用的区别")
    require("不自动创建网页会话" in usage and "不支持普通深研 task_id 或通用 AI 异步任务取消" in usage,
            "网页会话与异步任务边界不清")
    require("已经公开的分享快照会独立保留" in usage and "make_public:true" in usage,
            "公开分享确认或独立快照边界缺失")
    for document in (readme, usage, skill):
        for marker in ("submit_kb_question", "regenerate_kb_answer", "generation_id",
                       "include_original_native=true", "读取不自动恢复", "agent_steps",
                       "最近 3 轮", "最近 5 版", "部分新回答", "刷新工具列表",
                       "2026-10-14.2", "original_native_offset=0", "original_native_snapshot_chunk",
                       "next_offset", "base64", "bytes", "snapshot_sha256",
                       "total_bytes", "不能逐页先解码 UTF-8", "≤262144 bytes",
                       "小对象只接受offset=0", "offset达到或超过total_bytes",
                       "保留原 generation_id", "不要省略 generation_id 降级为消息级停止"):
            require(marker in document, f"原生知识库安全使用说明缺 {marker}")
        for stale in ("不提供新建网页会话或重新生成回答入口", "仅网页可取消消息",
                      "四个付费提交工具"):
            require(stale not in document, f"原生知识库仍有旧能力边界: {stale}")
    task_section = usage.split("#### `get_research_task`", 1)[1].split("\n#### `", 1)[0]
    require("| `original_native_offset` | int | 否 | 0 |" in task_section,
            "快照分页缺可选字节偏移参数表")
    require("snapshot_only" in usage and "recovery_snapshot_id" in usage,
            "完整快照只读与恢复标识缺失")
    require("`generation_id`" in usage.split("#### `stop_kb_generation`", 1)[1].split("\n#### `", 1)[0],
            "停止工具缺可选轮次字段")
    verify_boundary_self_checks()
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
    require(plugin["version"] == "2.6.3", "插件材料版本未升级到 2.6.3")
    require("## 2026-10-16 · 2.6.3 接入材料" in changelog, "CHANGELOG 缺本次材料版本记录")
    for manifest_text in (plugin["description"], marketplace["plugins"][0]["description"]):
        require("28" in manifest_text and "2.6.3 接入材料" in manifest_text
                and "候选" not in manifest_text and "尚未发布" not in manifest_text,
                "插件清单缺 Standard 28 工具正式口径")
        require("全球宏观" in manifest_text, "插件清单缺全球宏观能力")
    require(marketplace["plugins"][0]["name"] == plugin["name"], "marketplace/plugin 名称漂移")
    require("adamas" in mcp["mcpServers"], "插件缺 adamas MCP 配置")
    print("PASS: public Standard contract is internally consistent")


if __name__ == "__main__":
    main()
