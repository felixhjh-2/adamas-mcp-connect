# ADAMAS MCP — 接入仓库

> 把 ADAMAS 投研能力接进你自己的 AI:产业景气度、产业链传导图谱、公司跟踪、全球宏观、
> 模型选股、每日信息流、深度研究与纪要生成 —— **一个 MCP 端点,Standard 档 15 个工具**。

- **端点**:`https://www.adamas-research.com/mcp`(remote MCP,streamable HTTP,无需安装任何服务)
- **认证**:Bearer key，或客户端原生 OAuth（public client + PKCE）
- **完整文档**:[docs/USAGE.md](docs/USAGE.md)(全部工具的参数/返回/示例/配额/FAQ)

> 本仓库只包含接入材料(文档 / Skill / 示例),服务本体由 ADAMAS 托管运行。
> Bearer 方式需要 ADAMAS API key；OAuth 方式无需手工填写 key 或 client secret，
> 但登录的 ADAMAS 账号仍需已开通 MCP 权限与配额。
>
> 两种接入方式:**Bearer key 手工配置**(能为 remote MCP 自定义 HTTP header 的客户端),或
> **OAuth 自动授权**(ChatGPT、Claude Code 及其他兼容客户端,只填端点 URL、
> 客户端自动发现授权并绑定你的 ADAMAS 账号,无需手工填 key)。

## 30 秒接入

### WorkBuddy(腾讯)

设置 → 连接器 → 自定义连接器:

| 配置项 | 值 |
|---|---|
| 连接器类型 | MCP(streamable HTTP) |
| URL | `https://www.adamas-research.com/mcp` |
| 请求头 | `Authorization: Bearer <your-api-key>` |

建议同时导入配套 Skill(见下文「安装 Skill」),让你的 agent 按 ADAMAS 推荐的方法论用这些工具。

### Kimi Code

Kimi Code 原生支持 remote HTTP MCP,并可通过环境变量读取 Bearer key。在
`~/.kimi-code/mcp.json`(或当前项目的 `.kimi-code/mcp.json`)中加入:

```json
{
  "mcpServers": {
    "adamas": {
      "url": "https://www.adamas-research.com/mcp",
      "bearerTokenEnvVar": "ADAMAS_API_KEY"
    }
  }
}
```

向启动 Kimi Code 的进程注入 `ADAMAS_API_KEY`,值只填原始 `adamas_...` key,
不要带 `Bearer ` 前缀。新开会话后用 `/mcp` 查看连接状态与工具清单。
Kimi Code for VS Code 也支持 HTTP MCP;当扩展与 CLI 使用同一 `KIMI_CODE_HOME`
时会共享上述 MCP 配置。详见
[Kimi Code CLI MCP 文档](https://www.kimi.com/code/docs/kimi-code-cli/customization/mcp.html)、
[Kimi Code for VS Code 文档](https://www.kimi.com/code/docs/kimi-code-for-vscode/customization.html)
和[扩展官方说明](https://github.com/MoonshotAI/kimi-code/tree/main/apps/vscode)。

> 这里的 Kimi 接入特指 **Kimi Code**;普通 Kimi 网页/App 不使用这份本地 MCP 配置。

### Claude Code

推荐直接使用 OAuth，无需 API key 或自定义请求头：

```bash
claude mcp add --transport http adamas https://www.adamas-research.com/mcp
claude mcp login adamas
```

第二行也可改为启动 Claude Code 后输入 `/mcp`，选择 `adamas` 并完成
Authenticate。浏览器会打开 ADAMAS 授权页；先登录已开通 MCP 权限的 ADAMAS
账号，再同意授权。参见
[Claude Code 官方 MCP 文档](https://code.claude.com/docs/en/mcp)。

无人值守或明确使用 Bearer key 时，也可配置请求头：

```bash
claude mcp add adamas --transport http https://www.adamas-research.com/mcp \
  --header "Authorization: Bearer <your-api-key>"
```

本仓库现有 Claude Code 插件用于一步装齐 MCP 连接和 Skill 方法论，连接仍采用
`ADAMAS_API_KEY` Bearer key；希望使用 OAuth 时请按上面的无请求头命令直连，
再手动复制 Skill，或只把插件当作 Bearer 方案使用：

```bash
export ADAMAS_API_KEY=<your-api-key>          # 建议写进 shell profile
claude  # 会话内执行:
#   /plugin marketplace add felixhjh-2/adamas-mcp-connect
#   /plugin install adamas-research-report@adamas
```

### Codex

在 `~/.codex/config.toml`(或已信任项目的 `.codex/config.toml`)中加入:

```toml
[mcp_servers.adamas]
url = "https://www.adamas-research.com/mcp"
bearer_token_env_var = "ADAMAS_API_KEY"
default_tools_approval_mode = "writes"
```

用密码管理器或 shell profile 向启动 Codex 的进程注入 `ADAMAS_API_KEY`,
不要把 key 写进 `config.toml`。重启 Codex 后可用 `/mcp` 查看连接与工具。

### Cursor

在 Cursor 的 `~/.cursor/mcp.json` 中加入:

```json
{
  "mcpServers": {
    "adamas": {
      "url": "https://www.adamas-research.com/mcp",
      "headers": { "Authorization": "Bearer ${env:ADAMAS_API_KEY}" }
    }
  }
}
```

向启动 Cursor 的进程注入 `ADAMAS_API_KEY` 后重启 Cursor。密钥不写进
`mcp.json`;Cursor 会按 `url` 自动使用 remote HTTP transport。

### ChatGPT / Claude / 其他 MCP 客户端 —— OAuth 自动授权

不支持自定义 remote MCP 请求头的客户端可用 **OAuth 自动授权,无需手工填 key 或 client secret**。

- **ChatGPT**：在 ChatGPT Web 的 Settings → Security and login 开启 Developer mode，
  再从 Plugins 的 `+`（部分界面显示为 Settings → Apps / Connectors → Create）添加远程 MCP。
  URL 填 `https://www.adamas-research.com/mcp`，不填请求头。完整 MCP 当前面向
  Business、Enterprise、Edu；Pro 在 Developer mode 下支持 read/fetch MCP。实际入口和
  可用能力还受工作区管理员策略影响。参见
  [OpenAI 接入步骤](https://developers.openai.com/plugins/deploy/connect-chatgpt)和
  [Developer mode / MCP 可用范围](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt-beta)。
- **Claude Code**：使用上文不带 `--header` 的 `claude mcp add`，再运行
  `claude mcp login adamas` 或在会话内用 `/mcp` 完成认证。
- **claude.ai / Claude Desktop 及其他客户端**：若该版本提供自定义
  Apps / Connectors / MCP 入口，添加同一 URL 且不填请求头；具体入口与可用范围以客户端为准。

保存或连接后会自动跳转 ADAMAS 授权页；**需先在 `www.adamas-research.com` 登录已开通
MCP 权限的 ADAMAS 账号**，在授权页点“同意并连接”即可完成绑定。

服务端采用 Authorization Code + S256 PKCE；public client 使用
`token_endpoint_auth_method=none`，无需 `client_secret`，并支持 refresh token
轮换，客户端可在访问令牌过期后续期而无需反复登录。

默认支持 `chatgpt.com`、`claude.ai`、`claude.com`、`www.cursor.com`、`vscode.dev`、
`insiders.vscode.dev`，以及
`localhost` / `127.0.0.1` / `::1` 本机回调。网页回调路径可动态变化，不必写死；远端仅允许
HTTPS，且不接受任意网站或通配子域。(`claude_desktop_config.json` 只配本地 server,不用于此。)

### 自建 agent(Python)

见 [examples/quickstart.py](examples/quickstart.py):

```bash
python -m pip install "mcp>=1.28.1,<2"
ADAMAS_API_KEY=<your-api-key> python examples/quickstart.py
```

## 能做什么(Standard 档 15 个工具速览)

| 能力域 | 工具 |
|---|---|
| 资产解析 | `search_assets`(名称/代码 → 标准信息+行业分类) |
| 产业 | `get_industry_scores`(景气度+六维趋势)`get_industry_graph`(产业链传导图谱)`get_industry_report`(报告 PDF) |
| 公司 | `check_company_coverage`(批量查覆盖)`get_company_tracking`(跟踪报告全文,含历史期) |
| 全球宏观 | `get_global_macro`(国别九维度最新报告) |
| 选股 | `get_model_picks`(最新已发布的量化选股 Top N);`submit_stock_screen`(产业链选股,异步) |
| 信息流 | `get_info_feed`(当日要闻打分摘要) |
| 研究成稿 | `submit_deep_research`(深度研究问答,异步)`submit_notes_report`(深度纪要+PDF,异步)`get_strategy_reports`(沙盘推演报告) |
| 入口 | `list_capabilities`(能力地图,每个会话第一站)`get_research_task`(异步任务轮询) |

典型玩法:让你的 AI 写行业跟踪简报、盘前扫当日高分要闻、比较不同经济体的宏观九维度、推演产业链传导、
把研究问题外包给 ADAMAS 研究引擎、一键产出深度纪要 PDF。方法论详见 Skill。

## 安装 Skill(可选,强烈推荐)

Skill 是「怎么用好这些工具」的方法论包:先看地图再取数、标的先解析代码、
数据与观点分开写、限流退避、成文规范(数据标注日期、免责声明原文保留)。

- **WorkBuddy / OpenClaw**:下载本仓库,把 `plugins/adamas-research-report/skills/adamas-research-report/`
  整个目录作为技能导入(技能管理 → 导入本地技能包);
- **Kimi Code**:把该目录复制到 `~/.kimi-code/skills/adamas-research-report/`
  (或项目 `.kimi-code/skills/adamas-research-report/`),新开会话后可用
  `/skill:adamas-research-report` 显式调用;
- **Claude Code**:上面的插件方式自动装;或手动拷贝该目录到项目 `.claude/skills/`;
- **其他 Agent 框架**:把该目录放进框架的 skills 目录即可(触发条件写在 SKILL.md frontmatter)。

## 申请 API key / 提额 / 支持

联系 ADAMAS 团队。key 按账号发放,支持有效期与配额管理。遇到问题先看 [docs/USAGE.md](docs/USAGE.md) 第 8 节 FAQ。

## 版本

见 [CHANGELOG.md](CHANGELOG.md)。文档与线上服务同步更新,以本仓库 main 为准。
