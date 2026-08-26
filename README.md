# ADAMAS MCP — 接入仓库

> 把 ADAMAS 投研能力接进你自己的 AI:产业景气度、产业链传导图谱、公司跟踪、全球宏观、
> 模型选股、每日信息流、深度研究与纪要生成 —— **一个 MCP 端点,Standard 档 15 个工具**。

- **端点**:`https://www.adamas-research.com/mcp`(remote MCP,streamable HTTP,无需安装任何服务)
- **认证**:`Authorization: Bearer <your-api-key>` —— API key 向 ADAMAS 团队申请
- **完整文档**:[docs/USAGE.md](docs/USAGE.md)(全部工具的参数/返回/示例/配额/FAQ)

> 本仓库只包含接入材料(文档 / Skill / 示例),服务本体由 ADAMAS 托管运行。
> 没有 API key 时以下配置可以先填好,拿到 key 即刻生效。
>
> 当前服务未实现 MCP OAuth discovery / 自动授权,需手工配置端点和 Bearer key。
> 不能为 remote MCP 设置自定义 HTTP header 的客户端暂不能直接接入。

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

```bash
claude mcp add adamas --transport http https://www.adamas-research.com/mcp \
  --header "Authorization: Bearer <your-api-key>"
```

或者用插件一步装齐(MCP 连接 + Skill 方法论一起装,key 走环境变量):

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

### Claude Desktop

ADAMAS 当前的自定义 Bearer 认证不能直接配置进 Claude Desktop 的 remote
connector。Claude Desktop 的 remote MCP 需从 Settings → Connectors 添加,
当前界面提供免认证或 OAuth 流程;
`claude_desktop_config.json` 只配置本地 server,不能用来连接这种带自定义
Bearer header 的 remote server。请改用 Kimi Code、Claude Code、Cursor、Codex 或 WorkBuddy。

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
