# ADAMAS MCP — 接入仓库

> 把 ADAMAS 投研能力接进你自己的 AI:产业景气度、产业链传导图谱、公司跟踪、全球宏观、
> 模型选股、每日信息流、深度研究与纪要生成 —— **一个 MCP 端点,Standard 档 26 个工具**。

> **接入材料（2.5.0，2026-10-14）**：本文与配套 Skill 对应本版本的 Standard 契约。
> 当前 key 实际可用工具和参数以 `tools/list`、`prompts/list` 与 `list_capabilities().service` 为准。

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

## 能做什么(Standard 档 26 个工具速览)

| 能力域 | 工具 |
|---|---|
| 资产解析 | `search_assets`(名称/代码 → 标准信息+行业分类) |
| 产业 | `get_industry_scores`(景气度+六维趋势)`get_industry_graph`(产业链传导图谱)`get_industry_report`(报告 PDF) |
| 公司 | `submit_company_roundtable`(指定公司与报告期数的横向研究,异步);`check_company_coverage`(批量查覆盖,支持代码/简称，歧义需确认)`get_company_tracking`(跟踪报告与历史目录，明示正文交付状态) |
| 全球宏观 | `get_global_macro`(国别九维度最新报告) |
| 选股 | `get_model_picks`(最新已发布的量化选股 Top N);`submit_stock_screen`(产业链选股,异步) |
| 信息流与历史 | `get_info_feed`(最新文件摘要，明示日期与是否过期);`get_hot_notes`(按日期翻阅热点纪要及正文) |
| 网页知识库 | `list_kb_conversations` `get_kb_conversation`(本人会话与消息);`update_kb_message` `delete_kb_conversation`(编辑或删除);`share_kb_content` `manage_kb_shares`(公开分享与撤销);`stop_kb_generation`(仅网页可取消消息) |
| 研究成稿 | `submit_deep_research`(深度研究问答,异步)`submit_notes_report`(深度纪要+PDF,异步)`get_strategy_reports`(沙盘推演报告) |
| 入口与恢复 | `list_capabilities`(授权目录、工作流与数据地图)`get_my_quota`(额度自查)`list_my_research_tasks`(任务历史与回执恢复)`get_research_task`(异步任务轮询) |

典型玩法:让你的 AI 写行业跟踪简报、盘前核对最新高分要闻、比较不同经济体的宏观九维度、推演产业链传导、
把研究问题外包给 ADAMAS 研究引擎、一键产出深度纪要 PDF。方法论详见 Skill。

首次会话先查能力地图，批量调用或提交研究前用 `get_my_quota` 自查；它免日额度扣减，仍受请求频率限制。

`POST /mcp` 的完整 UTF-8 JSON-RPC 请求体（协议字段及全部参数）最多 **1 MiB（1048576 bytes）**；可查看 `list_capabilities().transport.request_limits`。
字段字符上限不等于完整请求字节上限，中文、emoji、JSON 转义和空白都计入实际传输字节。

编辑消息时，`changes.versions` 最多20项，每项≤399996个Unicode字符；完整数组按
`json.dumps(versions, ensure_ascii=False)` 默认格式序列化后≤400000个Unicode字符，
含括号、引号、转义、逗号和空格。非ASCII字符不转义，元素之间用逗号加一个空格分隔。
这些字段限制同时生效，仍须满足完整 UTF-8 JSON-RPC 请求体的 1 MiB 上限。

完整请求体超过 1 MiB 时返回 HTTP 413，本次请求未进入工具业务；不能据此推断此前受理状态未知的提交未被受理，先核对原任务或原资源。
不自动截断文本、丢弃 history 或 versions，也不换键重投写入或收费操作。大文本可用网页编辑，或由用户明确缩小输入范围后再操作。

研究提交回执丢失时，先用 `list_my_research_tasks` 找回 task_id，再轮询。
付费四个提交工具支持可选 `idem_key`（≤128 个 ASCII 字符，`[A-Za-z0-9][A-Za-z0-9_.:-]*`）：同一 key、同一工具内同键同完整业务参数返回原任务，不重复扣本次账号用量。深研 `session_id` 也必须一致；同键换参为 `BadParam`。无键每次 RPC 仍新建意图，但回执与本版本创建任务的轮询会返回生成的 `auto:<UUIDhex>` 恢复键；丢回执先历史找 task_id，再轮询取键，需要恢复提交时显式传返回键与完整原参数。轮询不会自动重新派发付费任务，新键不等于恢复原任务。 持久付费任务还匹配原绑定账号；改绑不转让历史，更换账号应重新签发 key。旧游标失效时从第一页重取。
回执新增 `idempotency_persisted`，可能带 `progress` / `task_status`；这不证明研究引擎已受理。状态未知先查历史/轮询，不能盲目重投或推断已退款。
历史按 `has_more` / `next_cursor` 翻页，保留原 status / kind；历史是落库摘要，当前状态与结果用轮询工具获取。
网页会话 ID、消息 ID 与研究 task_id 分别管理；深研不会自动创建网页会话。公开分享须用户明确同意，删除会话不撤销分享快照。停止网页生成返回 `cancel_requested` / `not_running` / `not_cancellable_here`；后者不表示已停止，也不支持取消异步研究或请求退款。热点历史用日期与游标翻页，不能当作实时新闻。
工具错误先读 `error_class` 与 `recovery`，仅 `retry_safe=true` 时自动重放，不盲目重复付费提交。

图谱返回焦点及一跳邻居，sector 同时限制两者；每条边的端点都在返回节点中。
公司名单先确认 `ambiguous`，全文先查 `meta.content_status`，截断正文不能当成全文。
信息流的日期来源于文件修改时间，先检查 `stale`；空文件未生成不代表市场没有新闻。
深度研究的 `doc_id_mapping` 可能为空；按 `citation_note` 使用可用映射，无映射保留原 E 编号，不编造文档标题或链接，也不承诺所有回答可审计。

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

见 [CHANGELOG.md](CHANGELOG.md)。2.5.0 接入材料；服务升级期间实际支持范围以当前端点发现结果为准。
