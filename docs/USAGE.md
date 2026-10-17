# ADAMAS MCP 使用文档

> **接入材料（2.6.5，2026-10-17）**：当前可用工具与参数以 `tools/list`、`prompts/list` 和 `list_capabilities().service` 为准。

> 面向外部集成方。读完本文即可把 ADAMAS 投研能力接进你自己的 agent / IDE / 办公工具。

## 1. 概述

ADAMAS MCP 是 ADAMAS 金融投研平台的对外能力分发服务,以
**remote MCP server(streamable HTTP)** 形态提供。它适配能配置自定义
remote MCP endpoint 与 `Authorization: Bearer` 请求头的客户端
(WorkBuddy、Kimi Code、Claude Code、Cursor、Codex、自建 agent 框架等)。

> **两种接入方式**:能为 remote MCP 自定义 HTTP header 的客户端用 **Bearer key**(端点 +
> `Authorization: Bearer <key>`);ChatGPT、Claude Code 及其他兼容客户端也可走
> **OAuth 自动授权**(只填端点 URL,客户端自动发现授权并绑定你的 ADAMAS 账号,无需手工填 key
> 或 client secret，但账号仍需已开通 MCP 权限与配额，见 2.6)。

它对外提供八类投研能力:

| 能力域 | 说明 |
|---|---|
| 产业景气度 | 约 190 个产业的景气度打分、六维趋势、跟踪摘要与历史快照 |
| 产业报告 | 边际跟踪报告与完整深度报告的 PDF 下载(成稿报告直接给最终用户) |
| 产业关联图谱 | 约 190 个产业节点 + 产业链传导关系边(方向/强度/时滞),支持传导链推演 |
| 公司跟踪 | 约 2400 家公司的跟踪报告全文(markdown,含历史期)与历史目录 |
| 全球宏观 | 分经济体的九维度报告覆盖与最新正文 |
| 每日信息流 | 多源聚合后二次加工的最新文件摘要，明示文件日期与 stale(晨会/盘前场景) |
| 模型与产业链选股 | 最新已发布的量化选股 Top N(排名股票/资产,秒级只读)与产业链量化选股任务(异步) |
| 深度研究与纪要 | 深度研究问答、深度纪要报告生成(异步任务) |

- **端点**:`https://www.adamas-research.com/mcp`
- **传输**:MCP streamable HTTP(无状态,支持断线重连后重新调用)
- **认证**:二选一 —— 每个请求携带 `Authorization: Bearer <your-api-key>`（API key 向 ADAMAS 申请），或使用客户端原生 OAuth 自动授权（public client + S256 PKCE，无需手工 key/secret）
- **内容**:本公开主文档对应 Standard 档,**28 个工具**(22 个 data 类入口 + 6 个 research 提交工具，含额度自查与任务历史)+ 2 个预置 prompts + 1 个 Agent Skill 包。Standard 包含最新已发布的量化选股结果、产业链量化选股与全球宏观入口。本公开文档只描述 Standard 契约。

两类工具的契约有本质区别,集成前务必理解(详见第 3、6 节):

- **data 类**:客观数据、已发布模型结果与已成稿报告,秒级返回,配额宽;
- **research 类**:含模型生成的分析观点,**异步任务对**(提交 → 轮询),配额窄,结果强制附带免责声明,**引用时必须原文保留**;

## 2. 快速开始

以下配置中的 `<your-api-key>` 均替换为 ADAMAS 发放给你的 API key。

### 2.1 WorkBuddy(腾讯)

设置 → 连接器 → 自定义连接器,按下表填写:

| 配置项 | 值 |
|---|---|
| 连接器类型 | MCP(streamable HTTP) |
| URL | `https://www.adamas-research.com/mcp` |
| 请求头 | `Authorization: Bearer <your-api-key>` |

保存后,在会话中即可看到 `list_capabilities`、`get_industry_scores` 等工具。建议同时安装配套 Skill(见第 7 节),让 agent 按 ADAMAS 推荐的方法论用这些工具。

### 2.2 Kimi Code

Kimi Code CLI 原生支持 remote HTTP MCP,并支持通过 `bearerTokenEnvVar` 从环境变量
读取 Bearer token。先向启动 Kimi Code 的进程注入 key:

```bash
export ADAMAS_API_KEY=<your-api-key>
```

再在用户级 `~/.kimi-code/mcp.json`(跨项目共享),或当前项目的
`.kimi-code/mcp.json` 中加入:

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

`url` 条目未写 `transport` 时,Kimi Code 会按 HTTP MCP 连接。保存后新开一个
Kimi Code 会话,输入 `/mcp` 查看 `adamas` 的连接状态与工具清单。也可在 TUI
运行 `/mcp-config` 管理 server。Kimi 官方说明:
[Model Context Protocol](https://www.kimi.com/code/docs/kimi-code-cli/customization/mcp.html)。

`ADAMAS_API_KEY` 只填原始 `adamas_...` key,不要带 `Bearer ` 前缀;
Kimi Code 会据此生成 `Authorization: Bearer <your-api-key>` 请求头。

Kimi Code for VS Code 同样支持 HTTP MCP。当扩展与 CLI 使用同一
`KIMI_CODE_HOME` 时会共享 `mcp.json`,因此可直接复用上述配置;同时确保启动
VS Code 的进程能读取 `ADAMAS_API_KEY`,然后新开会话。扩展内也可从齿轮菜单 →
MCP Servers 查看和测试连接。参见
[Kimi Code for VS Code 官方文档](https://www.kimi.com/code/docs/kimi-code-for-vscode/customization.html)
和[扩展官方说明](https://github.com/MoonshotAI/kimi-code/tree/main/apps/vscode)。

> 本节的“Kimi”特指 **Kimi Code CLI / Kimi Code for VS Code**。普通 Kimi
> 网页/App 不读取 `~/.kimi-code/mcp.json`,不能照搬这段本地配置。

### 2.3 Claude Code

推荐使用 OAuth，不带 `--header`：

```bash
claude mcp add --transport http adamas https://www.adamas-research.com/mcp
claude mcp login adamas
```

`claude mcp login adamas` 会打开浏览器完成 ADAMAS 登录与授权；也可启动 Claude Code，
在会话内输入 `/mcp`，选择 `adamas` → Authenticate。账号需已开通 MCP 权限。
验证时，`claude mcp list` 应显示 adamas 已连接，会话内 `/mcp` 可查看工具清单。
详见 [Claude Code 官方 MCP 文档](https://code.claude.com/docs/en/mcp)。

无人值守环境或明确使用 Bearer key 时，可改用：

```bash
claude mcp add adamas --transport http https://www.adamas-research.com/mcp \
  --header "Authorization: Bearer <your-api-key>"
```

本仓库的 Claude Code 插件会同时安装 MCP 连接与 Skill，但其内置连接当前仍读取
`ADAMAS_API_KEY` 并使用 Bearer key。需要 OAuth 时，请按本节无请求头命令直接连接，
并按第 7.2 节手动安装 Skill；不要在 OAuth 连接上同时保留旧的 Authorization 请求头。

### 2.4 Codex

在 `~/.codex/config.toml`(或已信任项目的 `.codex/config.toml`)中加入:

```toml
[mcp_servers.adamas]
url = "https://www.adamas-research.com/mcp"
bearer_token_env_var = "ADAMAS_API_KEY"
default_tools_approval_mode = "writes"
```

用密码管理器或 shell profile 向启动 Codex 的进程注入
`ADAMAS_API_KEY`,不要把 key 写进 `config.toml`。服务端工具带 MCP read/write
annotations;因此建议保留 `writes`:纯查询可自动调用,提交研究等非只读操作再请求
用户确认。重启 Codex 后可用 `/mcp` 查看连接与工具。

### 2.5 Cursor

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

### 2.6 ChatGPT / Claude / 其他 MCP 客户端 —— OAuth 自动授权

不支持自定义 remote MCP 请求头的客户端可用 **OAuth 自动授权,无需手工填 key 或 client secret**:

1. **ChatGPT Web**：到 Settings → Security and login 开启 Developer mode，再从
   ChatGPT Plugins 的 `+` 添加；部分界面显示为 Settings → Apps / Connectors → Create。
   完整 MCP 当前面向 Business、Enterprise、Edu；Pro 在 Developer mode 下支持
   read/fetch MCP。入口和可用能力还可能受工作区管理员策略限制;
2. **Claude Code**：执行 2.3 节不带 `--header` 的 `claude mcp add`，再运行
   `claude mcp login adamas`，或在会话内用 `/mcp` 选择 Authenticate;
3. **claude.ai / Claude Desktop 及其他客户端**：仅当该版本提供自定义
   Apps / Connectors / MCP 入口时添加；具体入口与可用范围以客户端为准;
4. **URL** 统一填 `https://www.adamas-research.com/mcp`(MCP / streamable HTTP),不填任何请求头;
5. 保存后点连接,客户端自动发现 ADAMAS 授权服务并跳转授权页;
6. **前提**:你需已在 `www.adamas-research.com` 登录已开通 MCP 权限的 ADAMAS 账号
   (授权页复用该登录态),
   在授权页点"同意并连接"完成绑定后自动跳回;
7. 连接成功即可在会话中看到工具;可用工具与配额由账号档位决定。

服务端默认按**精确主机名**支持以下回调，路径可由客户端动态生成：
`chatgpt.com`、`claude.ai`、`claude.com`、`www.cursor.com`、`vscode.dev`、
`insiders.vscode.dev`，以及
`localhost` / `127.0.0.1` / `::1` 本机回调（适用于使用 loopback 的 Kimi Code、
Windsurf、Cursor、VS Code 等桌面端）。远端回调强制 HTTPS，本机回调可用 HTTP；
不会为任意网站或通配子域开放授权码回跳。

客户端侧参考：[ChatGPT Developer mode 与 Plugins 接入](https://developers.openai.com/plugins/deploy/connect-chatgpt)、
[ChatGPT Developer mode / MCP 可用范围](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt-beta)、
[Claude Code MCP 与 OAuth](https://code.claude.com/docs/en/mcp)、
[Cursor MCP OAuth 回调](https://cursor.com/docs/mcp)、
[VS Code MCP 授权](https://code.visualstudio.com/api/extension-guides/ai/mcp)。

`token_endpoint_auth_method=none` 的公共客户端无需 `client_secret`：token 端点会校验
一次性授权码、注册时的精确 redirect URI 与 S256 PKCE `code_verifier`，并签发可轮换的
refresh token，让兼容客户端在访问令牌过期后续期而无需反复登录。若客户端使用
`client_secret_post/basic`，服务端只保存 secret 的 SHA-256，并在换 token 时校验。

(`claude_desktop_config.json` 只配本地 server,不用于连接本 remote 服务。)

### 2.7 自建 agent(Python,官方 mcp SDK)

先安装已验证的新客户端 API 版本:

```bash
python -m pip install "mcp>=1.28.1,<2"
```

```python
import asyncio, json
import httpx
from mcp import ClientSession
try:
    from mcp.client.streamable_http import streamable_http_client
except ImportError:
    from mcp.client.streamable_http import streamablehttp_client as streamable_http_client

URL = "https://www.adamas-research.com/mcp"
HEADERS = {"Authorization": "Bearer <your-api-key>"}

def parse(result):
    """优先取 structured output;老版本客户端/SDK 拿不到时回退解析 JSON 文本,
    两种形态内容等价。"""
    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(result.content[0].text)

async def main():
    async with (
        httpx.AsyncClient(headers=HEADERS) as http_client,
        streamable_http_client(URL, http_client=http_client) as (read, write, _),
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1) 列出工具
            tools = await session.list_tools()
            print([t.name for t in tools.tools])

            # 2) 第一站:能力地图与数据新鲜度
            caps = parse(await session.call_tool("list_capabilities", {}))
            print(caps["freshness"])

            # 3) 产业景气度 + 最新高分信息流(另检查 stale)
            ind = parse(await session.call_tool("get_industry_scores", {"industry": "存储"}))
            print(ind["industries"][0]["name"], ind["industries"][0]["score"])
            feed = parse(await session.call_tool("get_info_feed", {"limit": 3}))
            print([it["title"] for it in feed.get("items", [])])

asyncio.run(main())
```

工具返回同时携带 structured output(`result.structuredContent`,JSON dict)与等价的 JSON 文本(TextContent);上例的 `parse` 两者都兼容,建议照抄。agent 类客户端(Kimi Code / Claude Code / WorkBuddy / Cursor 等)无需关心,模型直接读 JSON。

### 2.8 接入后的第一次调用(约定)

1. **先调 `list_capabilities`**:拿授权工具目录/工作流(`service`)、覆盖范围与各数据域新鲜度(`freshness`),行情为交易日盘后导入,别把旧数据当今天的；精确参数 schema 以 `tools/list` 为准;
2. **标的名可先解析**:用 `search_assets` 把公司名/代码解析成标准信息(行业分类/市场风格属性);
3. **所有数值以返回中的 `as_of` 为准**;
4. **错误先看 `error_class` 与 `recovery`**，结合可选 `retry_after_seconds` 处理，不要密集或盲目重试。
5. **全球宏观先无参调用** `get_global_macro()`:从返回的覆盖全景取
   `country_key`、九维度及最新报告日期,再按需取正文。
6. **批量任务前自查 `get_my_quota`**；研究提交回执丢失时先用 `list_my_research_tasks` 找回 task_id，再轮询，不要直接再次提交。

## 3. 工具参考

通用约定:

- 所有工具返回 JSON dict。业务层错误(参数错误、未找到、配额超限等)保留 `error` 并把 MCP `CallToolResult.isError` 标为 `true`；本版本返回 `error_class` 与 `recovery:{action,retry_safe,...}`，可退避错误还带 `retry_after_seconds`。SDK 通常仍会返回 `CallToolResult`，agent 应同时处理 `isError` 与 JSON 中的 `error`，不能只看 HTTP 200;
- `recovery.action` 可能为 `revise_input`(修改参数)、`stop`(停止)、`check_access`(检查权限)、`check_quota`(检查额度)、`wait`(等待)、`check_task_history`(先恢复任务)或 `contact_support`(联系支持)。仅在 `retry_safe=true` 时自动重放；付费研究提交结果不明时先查 `list_my_research_tasks`，不要直接重复提交。`retry_after_seconds` 是等待指引，不单独代表可以安全重放;
- 数据类返回的 `meta` 解释口径，观点相关的还含 `disclaimer`；数值使用自身 `as_of`，不要拿查询时间补齐缺失的数据日期。目录/状态响应不一定包含数值截止日;
- 日期输入使用 `YYYY-MM-DD`；时间戳字段可能带时区，例如产业 `summary_as_of`、任务时间与信息流 `source_updated_at`。信息流 `as_of` 是文件修改日期，不是每条事件发布日期。

### 3.1 data 类(客观数据与已发布结果,秒级返回)

---

#### `list_capabilities` — 能力地图(建议每个会话的第一站)

**用途**:返回资产覆盖统计、产业跟踪清单规模、公司报告库规模、各数据域最新截止日期。纯客观数据。

**参数**:无。

**返回结构要点**:

| 字段 | 说明 |
|---|---|
| `coverage.assets_total` | 资产总数 |
| `coverage.assets_by_class` | 按 L1 分类的资产数量分布 |
| `coverage.industries_tracked` | 跟踪产业数 |
| `coverage.company_reports` | `{reports: 报告总数, companies: 覆盖公司数}` |
| `industry_catalog` | **全部产业名**(约190个),产业类工具唯一有效的取值集合 —— 详见 `get_industry_scores` 一节的名称口径 |
| `freshness` | Standard 可见数据域的最新截止日:`model_picks_as_of`、`company_reports_latest` |
| `service` | `contract_version`、当前授权 `tools[]`、`workflows[]` 与 `usage` 指引。工具项包含 `name`、中文 `title`、`execution`、`quota`、`may_charge_credits`、`required_arguments`、`read_only`；精确类型与约束以 `tools/list` schema 为准 |
| `transport.request_limits` | 完整请求体限制：`method:"POST"`、`path:"/mcp"`、`max_body_bytes:1048576`、`encoding:"utf-8"`；超限 `exceeded_http_status:413`。字段字符限制不能覆盖此上限；agent 不自动截断、丢版本或重投写入 |
| `meta.note` | 口径说明 |

**示例**:

```jsonc
// 调用:list_capabilities()
// 返回(摘要,数值为示意):
{
  "coverage": {
    "assets_total": 2722,
    "assets_by_class": {"电子": 303, "医药生物": 201, "...": "..."},
    "industries_tracked": 189,
    "company_reports": {"reports": 3200, "companies": 2368}
  },
  "industry_catalog": ["3D打印", "AI应用", "AI模型", "CXO", "光伏", "固态电池", "…共约190个"],
  "freshness": {"model_picks_as_of": "2026-07-23", "company_reports_latest": "2026-07-24"},
  "meta": {"note": "freshness 即各数据域的截止日;所有数值以返回中的 as_of 为准"}
}
```

---

#### `get_my_quota` — 当前 key 配额自查

**用途**:查询当前 key 的档位级别、今日数据类/研究类额度与在途任务数。批量调用或提交研究前建议先查。

**参数**:无。

**返回结构要点**:`tier`、`tier_level`、`rpm_limit`、`data_daily` / `research_daily`(各含 `limit`、`used`、`remaining`)、`active_research_tasks`、`expires_at`(永久时为 `null`)与 `meta.resets_at`。它不扣 data/research 日额度，即使日额度已用完仍可自查，但仍受认证、RPM 和维护限制；不包含账号的完整用量账单。

---

#### `search_assets` — 资产模糊搜索

**用途**:按名称或代码模糊搜索资产,返回 `asset_code`(其他工具的输入主键)与行业分类、市场/风格属性。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `query` | string | 是 | — | 名称或代码片段,如 `"紫金"`、`"601899"` |
| `limit` | int | 否 | 10 | 返回条数,合法范围 1–50;越界为参数错误 |

**返回结构要点**:`matches[]`,每条含 `asset_code`、`asset_name`、`asset_class_l1`、`asset_class_l2`、`market_attribute`、`style_attribute`。排序规则:代码前缀命中 > 名称全等 > 名称短者优先。股份类别后缀(`A/B`、`-B/-W/-SW/-S/-R`)会先被归一化; 归一后仍未命中时,可能额外返回 `did_you_mean[]`(`{asset_code, asset_name}`),调用方应用候选代码重试。

**示例**:

```jsonc
// 调用:search_assets(query="紫金")
// 返回(摘要):
{
  "matches": [
    {
      "asset_code": "601899.SH", "asset_name": "紫金矿业",
      "asset_class_l1": "有色金属", "asset_class_l2": "工业金属",
      "market_attribute": "权益", "style_attribute": "周期"
    }
  ],
  "meta": {"note": "asset_code 是其他工具的输入主键;L1/L2 为申万式行业分类"}
}
```

---

#### `get_model_picks` — 最新已发布的量化选股 Top N

**用途**:读取 ADAMAS 量化选股模型最近一次已审核并发布的股票/资产打分结果。
这里排名的是**股票/资产**,不是不同 AI 模型。该调用不会现场重新运行选股,
通常秒级返回;结果含总分/百分位/预期收益及市场·风格·宏观分项,可按 L1 行业过滤。
例如 `top_n=10` 表示返回本期量化评分最靠前的 10 只股票/资产。
**非投资建议,引用需保留 `disclaimer`**。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `top_n` | int | 否 | 30 | 返回前 N 名,合法范围 1–100;越界为参数错误 |
| `asset_class_l1` | string | 否 | 不过滤 | 按 L1 行业精确过滤,如 `"有色金属"` |

**返回结构要点**:`as_of`(该期打分日)、`picks[]`(`{rank, asset_code,
asset_name, class_l1, total_score, percentile, expected_return,
components:{market, style, macro}}`,rank 越小越靠前,`percentile` 为 0–100 的百分位)、
`meta`(note + `disclaimer`)。

**示例**:

```jsonc
// 调用:get_model_picks(top_n=3)
// 返回(摘要,数值仅作结构示意):
{
  "as_of": "2026-07-23",
  "picks": [
    {"rank": 1, "asset_code": "600416.SH", "asset_name": "湘电股份",
     "class_l1": "电力设备", "total_score": 1.575, "percentile": 100.0,
     "expected_return": 0.318,
     "components": {"market": 0.421, "style": 0.539, "macro": 0.489}}
  ],
  "meta": {
    "note": "最新已发布的量化选股结果(排名对象是股票/资产,不是不同模型);rank 越小越靠前;非投资建议",
    "disclaimer": "本内容由 ADAMAS 模型生成,仅供研究参考,不构成任何投资建议;据此操作风险自担。引用时须保留本声明。"
  }
}
```

> `asset_class_l1` 使用资产表的 L1 分类,与 `industry_catalog` 中的 ADAMAS
> 细分产业不是同一套分类。不要把「光伏」「存储芯片」等细分产业名直接传给它;
> 不确定时省略该参数取全市场排名,再按研究主题筛选相关标的。

---

#### `get_industry_scores` — 产业景气度

**用途**:约 190 个产业的景气度打分、六维趋势(当前/预期/供给/成本/竞争/出口)、最新跟踪摘要及其时间;可选历史打分快照。**引用需保留 `disclaimer`**。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `industry` | string | 否 | 不传返回全部 | 产业名称,支持模糊匹配;不传时返回全部清单(按分数降序) |
| `include_history` | bool | 否 | false | 取历史打分快照;**仅在同时传了 `industry` 时生效** |
| `include_summary` | bool | 否 | true | 传 `false` 省略 `tracking_summary` 全文,其余字段不变 |

**返回结构要点**:`industries[]`,每条含 `name`、`sector`、`score`、`trends`(六个维度,值为方向符号文本:`↗` 改善 / `→` 持平 / `↘` 恶化)、`tracking_summary`(最新跟踪摘要)、`summary_as_of`;`include_history=true` 时另含 `score_history[]`(`{date, score}`)。未匹配到产业时返回 error，`did_you_mean` 最多给 5 个相近候选；完整合法名称取自 `list_capabilities().industry_catalog`，不要依赖不存在的 `available_industries` 字段。

> **⚠️ 产业名称口径**:本工具只认 ADAMAS 自建的**细分产业名**(如「光伏」「固态电池」「CXO」),**不认**申万/中信的一级行业名 —— 没有「新能源」「医药生物」「电力设备」这类。查之前先用 `list_capabilities` 的 `industry_catalog` 对齐名称。

> **📦 按体量选调用方式**(2026-08-10 实测,189 个产业;摘要每天更新,绝对值会浮动):
> | 你想要什么 | 怎么调 | 返回体量 |
> |---|---|---|
> | 确认产业名怎么写 | `list_capabilities` → `industry_catalog` | 约 2 KB |
> | 某个产业的摘要全文 | `get_industry_scores(industry="光伏")` | 约 1 KB |
> | 按分数/趋势筛产业 | `get_industry_scores(include_summary=false)` | 约 43 KB |
> | 全景通读所有摘要 | `get_industry_scores()` 不带参数 | **约 220 KB** |
>
> 最后一行会把全部约 190 篇跟踪摘要一次灌进上下文,比其它几种大一到两个数量级。只在确实要通读时才这么用 —— 想筛产业请用 `include_summary=false`(约为全量的 1/5),挑出来之后再对那几个单查全文。全量返回的 `meta.size_warning` 里会给出**本次的实际体量**。

**示例**:

```jsonc
// 调用:get_industry_scores(industry="存储", include_history=true)
// 返回(摘要,取自真实调用):
{
  "industries": [
    {
      "name": "存储芯片", "sector": "科技", "score": 5.3,
      "trends": {"current": "→", "expected": "→", "supply": "↗", "cost": "→", "competition": "→", "export": "↗"},
      "tracking_summary": "2026年7月,存储芯片行业出现关键拐点信号…",
      "summary_as_of": "2026-07-20 16:06:22+00:00",
      "score_history": [{"date": "2026-06-13 16:00:00+00:00", "score": 2.7}, {"date": "…", "score": "…"}]
    }
  ],
  "count": 1,
  "meta": {
    "note": "景气度为 ADAMAS 产业跟踪体系打分;六维趋势为当前/预期/供给/成本/竞争/出口",
    "disclaimer": "本内容由 ADAMAS 模型生成,仅供研究参考,不构成任何投资建议;据此操作风险自担。引用时须保留本声明。"
  }
}
```

---

#### `get_company_tracking` — 公司跟踪报告

**用途**:按公司名取最新一期跟踪报告全文(markdown)与历史报告目录(最多 12 期),覆盖约 2400 家。**引用需保留 `disclaimer`**。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `company` | string | 是 | — | 公司名或标准资产代码；支持全角/空白/股份后缀归一化及唯一模糊命中，多个候选需先确认 |
| `include_content` | bool | 否 | true | 是否返回全文;false 时只返回目录 |
| `report_date` | string | 否 | 最新一期 | 取历史期全文(`YYYY-MM-DD`,从 `history` 目录中选;传错会返回可选日期表) |

**返回结构要点**:`company`、`latest_report_date`、`report_date`(所选期)、`history[]`(`{report_date, company}`)、`content`(所选期正文 markdown)、`meta`(note + `disclaimer`)。精确公司名优先；唯一模糊结果可命中，多个候选时返回 error、`matched_by:"ambiguous"` 与最多 10 个 `alternatives`，必须确认准确公司名后重查，不会自动选择第一家。未找到时可用 `did_you_mean` 修正输入；`%` / `_` 按字面查询，不是通配符。

`meta.content_status` 区分 `omitted`(未请求全文)、`complete`、`truncated` 与 `unavailable`。成功读取还带 `content_truncated`、`content_chars_returned`、`content_bytes_original`(上游未提供时为 null)和 `content_byte_limit`。默认读取上限 4MiB **字节**；`truncated` 仍是成功交付的部分正文，不能声称读完全文。`unavailable` 时保留目录、`content:""` 与旧 `content_error`，同时返回工具错误；存储配置缺失为 `error_class:"S3Misconfigured"`，取件失败为 `Upstream`。目录最多 12 期，不代表完整历史库。

> **拿到一批公司时先用 `check_company_coverage` 批量筛**,不要对本工具循环单查 —— 几十个往返又慢又会撞 60 次/分钟的频率限制,而且每次都把整篇报告全文拉回来。

**示例**:

```jsonc
// 调用:get_company_tracking(company="紫金矿业")
// 返回(摘要):
{
  "company": "紫金矿业",
  "latest_report_date": "2026-07-18",
  "history": [
    {"report_date": "2026-07-18", "company": "紫金矿业"},
    {"report_date": "2026-06-20", "company": "紫金矿业"}
  ],
  "content": "# 紫金矿业跟踪报告\n\n## 本期要点\n…(markdown 全文)",
  "meta": {
    "content_status": "complete",
    "content_truncated": false,
    "note": "ADAMAS 公司跟踪体系报告;content 为所选期正文 markdown",
    "disclaimer": "本内容由 ADAMAS 模型生成,仅供研究参考,不构成任何投资建议;据此操作风险自担。引用时须保留本声明。"
  }
}
```

---

#### `check_company_coverage` — 批量查覆盖(拿到股票池先用它)

**用途**:一次问清一批公司**有没有跟踪报告**,单次往返。拿到几十只的股票池、想先筛出「哪些我们有覆盖」再深入时用它。

> **不要对 `get_company_tracking` 循环单查**:几十个往返既慢又会撞 60 次/分钟的频率限制,而且会把每家的报告全文都捞回来。本工具只回「有没有 + 最新期 + 期数」。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `names` | string[] | 是 | — | 公司名或资产代码列表，**列表总数须为 1–100 项，每项为非空字符串**；调用前先 trim 并去掉空项，超过 100 项请分批；与全文查询共享归一化/歧义规则 |

**返回结构要点**:`covered[]`(`{company_name, latest_report_date, periods, asked_as[]}`)、`not_covered[]`(`{asked, asked_as[], did_you_mean?}`)、`ambiguous[]`(`{asked, asked_as[], matched_by:"ambiguous", alternatives[], matches_total}`)、兼容字段 `ignored[]` 与 `summary`。`ignored` 不表示接口会接收空白项：列表包含 trim 后的空字符串会使整次调用参数校验失败，须在调用前去空。同一规范公司只返回一条 covered，`asked_as` 保留原始输入；`summary.asked` 为非空输入数，`unique_companies` 为归一化结果组数，另有 `covered` / `not_covered` / `ambiguous` / `ignored` 计数。歧义项不计入 covered 或 not_covered；从 alternatives 确认后再查。取全文使用 `covered[].company_name`。

**示例**:

```jsonc
// 调用:check_company_coverage(names=["贵州茅台", "宁德时代", "某不存在公司XYZ"])
// 返回(结构示意，日期与期数不是当前覆盖承诺):
{
  "covered": [
    {"asked_as": ["贵州茅台"], "company_name": "贵州茅台", "latest_report_date": "2026-08-05", "periods": 5},
    {"asked_as": ["宁德时代"], "company_name": "宁德时代", "latest_report_date": "2026-08-07", "periods": 5}
  ],
  "not_covered": [{"asked": "某不存在公司XYZ", "asked_as": ["某不存在公司XYZ"]}],
  "ambiguous": [],
  "ignored": [],
  "summary": {"asked": 3, "unique_companies": 3, "covered": 2, "not_covered": 1, "ambiguous": 0, "ignored": 0},
  "meta": {"note": "covered 里的 company_name 是库中的标准名,取全文请用 get_company_tracking(company=该标准名)"}
}
```

---

#### `get_industry_report` — 产业报告 PDF

**用途**:取产业的**边际跟踪报告**(每期更新)与**完整深度报告**的 PDF 下载链接。适合把成稿报告直接交付给最终用户阅读。

**参数**:`industry`(必填,支持模糊匹配,最多返回 5 个产业)。

**返回结构要点**:`industries[]`,每条含 `name`、`sector`、`tracking_report_pdf_url`(边际跟踪报告)、`full_report_pdf_url`(完整报告)、`updated_at`。**下载链接 10 分钟有效**,过期重新调用即可;无报告的产业带 `note` 说明。含 `disclaimer`。

`meta.download_links_status` 表示本次下载链接的签名生成状态：`complete` 全部已提供的报告链接生成成功、`partial` 部分成功、`unavailable` 已登记报告但链接均生成失败、`not_provided` 未提供报告文件。它不证明文件存在或下载成功。生成失败时仍保留报告信息及已成功链接，并返回顶层 `error`、`error_class`（MCP `isError=true`）；已有成功链接可继续使用，不能把链接暂不可用说成“暂无报告”。

---

#### `get_industry_graph` — 产业关联图谱

**用途**:产业节点(景气打分 + 六维方向信号)与产业链**传导关系边**(方向 sign / 强度 strength / 时滞 delay_ticks / 传导通道 channel)。适合回答"上游 A 涨价会传导到谁、多快、多强"这类传导链推演问题。

**参数**:

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sector` | string | 否 | 按板块过滤:`tech` / `cycle` / `consumer` / `pharma` |
| `node` | string | 否 | 按产业名称字面片段匹配焦点，返回焦点及一跳相邻节点，不递归展开 |

不带参数返回全量图谱(约 190 节点 / 340+ 边)。

**返回结构要点**:`nodes[]`(`{node_id, name, layer, sector, score, score_source, signals}`)、`edges[]`(`{src, dst, type, strength, channel, delay_ticks, sign}`)、`counts`。`signals` 为 `{current, expected, supply, cost, competition, export}` 六维方向符号对象，与 `get_industry_scores.trends` 同源。`meta.matched_node_ids` 是焦点，`context_node_ids` 是补齐的一跳邻居，焦点排在前面；每条边的 src/dst 都存在于返回节点中。`sector` 是硬边界：同时限制焦点和邻居，跨板块边不返回；只有 sector 时返回该板块内的图。含 `disclaimer`。

---

#### `get_strategy_reports` — 策略沙盘推演报告

**用途**:按策略主题的沙盘推演报告 PDF 下载链接(10 分钟有效)。

**参数**:无。**返回**:`strategy_reports[]`(`{strategy, pdf_url, updated_at}`)、`meta`。含 `disclaimer`。

`meta.download_links_status` 同上：`complete` / `partial` / `unavailable` / `not_provided` 仅说明签名链接生成状态，不证明文件存在或下载成功。失败响应仍保留 `strategy_reports` 与已成功的 `pdf_url`，同时返回顶层 `error`、`error_class`（MCP `isError=true`）；不要把链接生成失败解读为没有报告。

---

#### `get_info_feed` — 最新市场信息流

**用途**:多源聚合后**二次加工**的最新文件摘要:每条为「重要性打分(10 分制)+ 标题 + 摘要正文」。通常每日北京时间早间更新，必须检查 `stale`，旧文件不能称为今日要闻。**披露口径:5 分以上**(与 ADAMAS 产品端一致;`min_score` 传低于 5 的值会被钳回下限,返回中 `min_score_applied` 为实际生效值)。典型场景:晨会准备、盘前核对最新高分要闻。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `limit` | int | 否 | 30 | 返回条数,合法范围 1–200;越界为参数错误 |
| `min_score` | float | 否 | 5(披露下限) | 合法范围 0–10;可传更高只看高分(如 `8`),0–5 之间的合法值仍按披露下限 5 执行;越界为参数错误 |

**返回结构要点**:`items[]`(`{score, title, body}`,按文件序)、`count`、`min_score_applied`、`as_of`、`source_updated_at`、`stale`、`availability`、`has_more` 与 `meta.matching_count`。`as_of`(上海日期)与 `source_updated_at`(带 +08:00 时间戳)都取自文件修改时间，`meta.freshness_source="file_mtime"`；它们不能证明每条事件的发生/发布日期。文件日期早于上海今天时 `stale=true,availability="stale"`；当前文件为 `available`。文件尚未生成时是 `not_generated`，时间与 stale 为 null、空列表，不能解读为市场没有新闻。当前文件经分数筛选为空仍为 available。`has_more` 表示匹配数超过 limit，本工具没有分页游标。文件更新中或解析失败返回明确错误与退避指引。条目**不含来源链接**，含 `disclaimer`。

---

#### `get_global_macro` — 全球宏观国别九维度报告

**用途**:先查有报告的经济体与九维度覆盖,再按经济体和维度
读取最新报告正文。全球宏观报告的跨度较长,每个经济体×维度只提供最新版,
不提供历史选择或跨期目录。只读、秒级返回;报告含模型生成的研究观点,
**引用时必须原文保留 `meta.disclaimer`**。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `country` | string | 否 | 不传返覆盖全景 | 经济体主键;必须取自无参返回的 `countries[].country_key` 或 `regions[].country_key` |
| `dimension` | string | 否 | 不传返该经济体的九维度覆盖 | 维度 key;必须与 `country` 一起传,取自 `dimensions[].key` 或 `cells[].key` |

为兼容滚动升级期间已缓存 schema 的旧客户端,当前工具 schema 暂保留 `report_date`。
它不再用于选择版本：省略即可；仅当所传值恰好等于当前最新版日期时兼容成功，
其他日期返回业务错误。新接入不要发送该字段。

**三种调用方式**:

| 调用 | 返回什么 |
|---|---|
| `get_global_macro()` | 覆盖全景:`countries[]`、`regions[]`、`dimensions[]`、`score_ready` |
| `get_global_macro(country="China")` | 中国的九个 `cells[]`,每格标出有无报告及最新日期 |
| `get_global_macro(country="China", dimension="industry")` | 中国“主导产业”最新正文 |

九个维度 key 是:`industry`(主导产业)、`consumption`(消费与服务业)、
`trade`(进出口)、`property`(建筑地产)、`inflation`(通胀)、`fiscal`(财政政策)、
`monetary`(货币政策)、`geopolitics`(外交&地缘)、`government`(政府动态)。

**覆盖全景返回要点**:

- `countries[]` 每条含 `country_key`、`country_name`、`dimensions`(0–9)、
  `latest_date`、`score`;
- `regions[]` 与上述结构相同,但是**非国家地区**。`China-Taiwan` 只会出现在
  `regions`,表示中国台湾地区;不得把它写成国家、并入 `countries` 或计入
  “覆盖国家数”;
- `dimensions[]` 含 `{key, label, order}`,是后续调用的唯一维度口径;
- `score_ready` 表示宏观周期打分模型是否已上线。当它为 `false` 时,
  `countries[].score` / `regions[].score` 为 `null`;集成方**不得臆造分数、推断排名或
  用颜色暗示尚不存在的周期信号**。

**经济体覆盖返回要点**:`country_key`、`country_name`、`cells[]`;
九个格子恒定返回,每格为 `{key, label, order, has_report, report_date}`。
没有报告的格子也会保留,此时 `has_report=false`、`report_date=""`;
这是正常空态,不是错误。

**报告正文返回要点**:`country_key`、`country_name`、`dimension`、`label`、
`report_date`(最新版日期)、`content`(markdown 正文)。
单篇正文超过输出上限时 `content` 会被截断,此时
`meta.content_truncated=true` 并给出 `meta.content_chars_original`;不得把截断内容
当作完整报告。
三种返回都带 `meta.note` 和 `meta.disclaimer`;返回的报告数据畸形或上游暂时不可达时,
工具会返回结构化 `error`,不会把不完整正文伪装成成功结果。

**示例**:

```jsonc
// 1) 调用:get_global_macro()
// 返回(摘要,日期为示意):
{
  "countries": [
    {"country_key": "China", "country_name": "中国", "dimensions": 9,
     "latest_date": "2026-08-04", "score": null}
  ],
  "regions": [
    {"country_key": "China-Taiwan", "country_name": "中国台湾地区", "dimensions": 9,
     "latest_date": "2026-08-04", "score": null}
  ],
  "dimensions": [
    {"key": "industry", "label": "主导产业", "order": 1},
    {"key": "consumption", "label": "消费与服务业", "order": 2}
    // 此处仅节选 2 项；真实成功响应固定返回完整 9 项。
  ],
  "score_ready": false,
  "meta": {
    "note": "…",
    "disclaimer": "本内容由 ADAMAS 模型生成,仅供研究参考,不构成任何投资建议;据此操作风险自担。引用时须保留本声明。"
  }
}
```

```jsonc
// 2) 调用:get_global_macro(country="China")
{
  "country_key": "China",
  "country_name": "中国",
  "cells": [
    {"key": "industry", "label": "主导产业", "order": 1,
     "has_report": true, "report_date": "2026-08-04"},
    {"key": "trade", "label": "进出口", "order": 3,
     "has_report": false, "report_date": ""}
    // 此处仅节选 2 格；真实成功响应固定返回完整 9 格。
  ],
  "meta": {"note": "…", "disclaimer": "…须原文保留…"}
}
```

```jsonc
// 3) 调用:get_global_macro(country="China", dimension="industry")
{
  "country_key": "China",
  "country_name": "中国",
  "dimension": "industry",
  "label": "主导产业",
  "report_date": "2026-08-04",
  "content": "# 中国·主导产业\n\n…(markdown 正文)",
  "meta": {"note": "…", "disclaimer": "…须原文保留…"}
}
```

---

### 3.2 research 类(含模型观点,异步任务对)

research 类与 data 类的契约区别:**结果含模型生成的分析观点**;走独立的日额度(默认每 key 每日 20 次提交)与全局并发闸;均为异步——提交秒回 `task_id`,用 `get_research_task` 轮询;结果强制附 `disclaimer`,**引用必须原文保留**。

**付费提交幂等**：六个提交工具均新增可选 `idem_key`，为空或省略时保留每次 RPC 创建新提交意图的旧行为。非空键必须为 1–128 个 ASCII 字符，匹配 `[A-Za-z0-9][A-Za-z0-9_.:-]*`。在同一 API key、同一工具内，同键与完整业务参数一致时返回原任务，不重复扣本次账号用量；跨 key 或跨工具不能恢复原任务。深度研究的 `question`、`mode`、`session_id` 都影响业务，重放必须保持一致。追问使用同一 session_id、不同 question 时是新业务，应使用新 idem_key。

同键换参返回 MCP 工具错误 `error_class="BadParam"`，不是 HTTP 409；恢复原任务须保留原键和原参数，明确提交新业务才使用新键。**新键不等于恢复原任务**。回执丢失或受理状态未知时，先用 `list_my_research_tasks` 找回 task_id，再用 `get_research_task` 查询原任务；不要盲目重投、换键或推断任务已取消、已退款。

**提交回执**保留 `task_id`、`status:"running"`、`eta_hint`、`next_step`，新增 `idem_key` 与 `idempotency_persisted:true`。显式传键时回显原键；为空或省略时返回为本次意图生成的 `auto:<UUIDhex>` 恢复键。本版本创建的付费任务在 `get_research_task` 中也返回该恢复键。需要恢复提交时，由调用者显式向同一工具传入返回的 `idem_key` 与完整原业务参数，才会恢复原意图；继续传空键仍会新建意图。轮询只查询、同步原任务状态，不会自动重新派发付费任务。

`idempotency_persisted:true` 只表示提交意图已记录，不证明研究引擎已受理或执行。受理待确认时可能带 `progress`，重放时可能带原任务的 `task_status`；外层 status 保留旧回执口径，任务当前状态与结果以轮询为准。失败响应若带 task_id，先查询该任务并按 `recovery` 处理。

---

#### `submit_deep_research` — 提交深度研究问题

**用途**:基于 ADAMAS 研究知识库 + 联网检索的深度研究问答(含模型观点)。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `question` | string | 是 | — | 研究问题 |
| `mode` | string | 否 | `"auto"` | `flash`(快,约 1–2 分钟)/ `auto`(自动,约 2–5 分钟)/ `plus`(深,约 5–10 分钟)/ `pro`(最深,约 8–12 分钟) |
| `session_id` | string | 否 | 空串 | 追问会话，非空时 ≤64 个 ASCII 字符，匹配 `[A-Za-z0-9_.:-]+`；同一话题复用；它纳入幂等业务参数 |
| `idem_key` | string | 否 | 空串 | 可选提交幂等键，≤128 个 ASCII 字符；同一次操作保留原键和完整业务参数，规则见上文 |

**会话隔离**：新提交的命名会话按当前 key 与绑定账号隔离。本次归属修正后，新提交不会自动接续升级前同名会话的上下文；需要延续时请在问题中补充必要背景。已受理任务仍按原 UUID、恢复键和完整原参数恢复，不改写其已保存请求。

**返回结构要点**(提交成功):`task_id`、`status: "running"`、`eta_hint`(耗时预期)、`next_step`(轮询指引)。可能的错误:mode 非法;并发已满(`retry_after_seconds: 120`);服务维护窗口暂停接单(`retry_after_seconds: 300`);研究引擎暂不可用。

**示例**:

```jsonc
// 调用:submit_deep_research(question="存储芯片本轮涨价周期还能持续多久?驱动因素是什么?", mode="plus", idem_key="storage-cycle-01")
// 返回:
{
  "task_id": "6f9c1e2a-…",
  "status": "running",
  "idem_key": "storage-cycle-01",
  "idempotency_persisted": true,
  "eta_hint": "约 5-10 分钟",
  "next_step": "用 get_research_task(task_id='6f9c1e2a-…') 轮询结果,建议间隔 ≥30 秒"
}
```

---

#### `submit_stock_screen` — 提交产业链量化选股

**用途**:按中文产业链名称触发选股流程,综合最新已发布的量化选股结果、相似度与产业链分析,
产出产业链图谱与候选标的(含模型观点)。约 3–8 分钟。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `industry_chain` | string | 是 | — | 产业链名称,1–200 字,如 `"存储芯片"`、`"光伏"` |
| `idem_key` | string | 否 | 空串 | 可选提交幂等键，≤128 个 ASCII 字符；同一次操作保留原键和 industry_chain，规则见上文 |

**返回结构要点**(提交成功):`task_id`、`status: "running"`、
`eta_hint: "约 3-8 分钟"`、`next_step`(建议轮询间隔 ≥60 秒)。选股全局同一时刻
只运行 1 个任务,并发已满时返回 error + `retry_after_seconds: 180`。

`done` 时 `result` 为选股引擎的完整结果对象,包含产业链图谱、候选公司与排名信息,
并带 `disclaimer`。本工具消耗 research 类 key 日额度及绑定账号的使用额度;
确认失败后按服务端结算结果处理本次账号用量，成功交付后不退；受理状态未知不等于失败或已退款。

**示例**:

```jsonc
// 调用:submit_stock_screen(industry_chain="存储芯片", idem_key="storage-screen-01")
{
  "task_id": "a31b7c90-…",
  "status": "running",
  "idem_key": "storage-screen-01",
  "idempotency_persisted": true,
  "eta_hint": "约 3-8 分钟",
  "next_step": "用 get_research_task(task_id='a31b7c90-…') 轮询结果,建议间隔 ≥60 秒"
}
```

---

#### `submit_notes_report` — 提交深度纪要报告

**用途**:深度纪要报告生成:多视角检索 + 深度推理 + 成稿(正文数千字,同时产出 PDF)。`topic` 既可以是研究主题(如「英伟达 GTC 大会要点」),也可以是一段会议/调研原始记录(≤2000 字)。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `topic` | string | 是 | — | 研究主题或会议原始记录，1–2000 字 |
| `idem_key` | string | 否 | 空串 | 可选提交幂等键，≤128 个 ASCII 字符；同一次操作保留原键和 topic，规则见上文 |

**返回结构要点**(提交成功):`task_id`、`status: "running"`、`eta_hint: "约 8-15 分钟"`、`next_step`(建议轮询间隔 ≥60 秒)。纪要生成全局同一时刻只跑 1 个,并发已满返回 error + `retry_after_seconds: 300`。

`done` 时的 `result`:`{title, markdown(纪要全文,直接给 AI 消费), pdf_download_url(PDF 成稿,3 天有效,给人阅读), pdf_download_expires_at, disclaimer}`。`markdown` 偶发拉取失败时为空串,此时用 `pdf_download_url`。

---

#### `submit_company_roundtable` — 多家公司报告横向研究

按明确选择的公司与报告期数生成横向问答，使用本次实际报告快照。先用
`search_assets` 确认资产代码，再检查公司报告覆盖；不要用通用深研替代指定报告的研究。

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `asset_codes` | string[] | 是 | — | 1–40 个资产代码，合并同公司后最多 10 家公司 |
| `question` | string | 是 | — | 1–2000 字的横向研究问题 |
| `periods` | int | 否 | 1 | 每家公司最近 1–3 期报告 |
| `history` | object[] | 否 | `[]` | 最多 12 轮已完成问答，每项为 `{question, answer}`；实际使用最近 6 轮。单项问题≤2000字、回答≤8000字 |
| `idem_key` | string | 否 | 空串 | 可选提交幂等键，≤128 个 ASCII 字符；同一次业务保留原键和完整参数 |

异步返回 `task_id`，按 `next_step` 用 `get_research_task` 轮询；完成结果含
`question`、`answer`、`engine:"company_roundtable"`、`report_count`、
`sources[]`（实际公司名与报告日期）和 `disclaimer`。报告材料过多时需减少公司或期数，
不能把未交付的报告视为已经用于回答。

它消耗研究提交额度和绑定账号的公司圆桌用量，与其他研究共享每 key 单任务限制。
历史问答由调用方显式传入，不自动创建网页知识库会话。网络断开不代表停止或退款；
回执不明先查原任务，重试保留全部参数（包括 history），不换键重投。

---

#### `submit_kb_question` — 原生网页知识库新建与续问

需本人有效绑定账号同时拥有 MCP 与知识库权限。新建或续问真实网页知识库会话，后续可在网页继续查看与提问；它与不自动创建网页会话的 `submit_deep_research` 分开。

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `question` | string | 是 | — | 原字符串 1–2000 个 Unicode 字符，去除首尾空白后不得为空；不接受 NUL 或无效 Unicode |
| `conversation_id` | int | 否 | 0 | 0 新建会话；正整数续问本人未删除会话 |
| `mode` | string | 否 | `auto` | `auto` / `flash` / `plus` / `pro`；pro 消耗 2 倍账号用量 |
| `idem_key` | string | 否 | 空串 | 可选幂等键，恢复原意图必须保留原键与全部参数 |

返回原 `task_id`（UUID）与同轮 `generation_id`；受理待确认时原生标识可能尚未返回，确认后提供正整数 `conversation_id` / `message_id` 与停止指引。用原 task_id 轮询，不把网页数字 ID 当作任务 UUID。服务从本人会话最近 3 轮已结束且有正文的问答构造上下文（包括保留的部分回答）；每轮问题截取至 2000 个 Unicode 字符、回答至 500 个 Unicode 字符，仅用于上下文，不改写已保存正文。调用方不传 session_id 或 history。

原生知识库完成结果的可选 `query` 返回站点保存的原问题，重新生成沿用该轮问题；旧后端可能为空。不要从回答正文猜测原问题。

网页和 MCP 后续提问在同一会话连续使用上述历史；空历史明确为空，不读取另一个隐式会话。生成中的会话不能并发开启下一轮，等待终态后再续问。

---

#### `regenerate_kb_answer` — 重新生成最新原生回答

只支持本人未删除会话中最新且已结束的助手消息；服务使用该回答对应的原问题，不允许调用方替换问题，也不从请求另选会话。

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `message_id` | int | 是 | — | 本人会话最新已结束助手消息的正整数 ID |
| `mode` | string | 否 | `auto` | `auto` / `flash` / `plus` / `pro`；pro 消耗 2 倍账号用量 |
| `idem_key` | string | 否 | 空串 | 可选幂等键，重放保持原消息 ID 与模式 |

保留原 task_id / generation_id；原生 conversation_id / message_id 在受理确认后返回，待确认时不能假定已经建好消息。上下文规则同新提问，但排除目标回答，避免把待重写答案当作历史。提交前独立保存原 content、agent_steps 与完整 versions；没有产生新回答时自动原样回退，有部分新回答则保存为新版本并计入本次用量。网页显示最近 5 版，原始完整快照独立保留，不能把可见版本截取误认为完整快照已被删除。

需要核对原版时，显式调用 `get_research_task(task_id=原任务, include_original_native=true)`。只读取原快照供核对及恢复所需数据；读取不自动恢复、重跑或再次结算。手动恢复 content / versions 必须由用户明确选择并满足编辑限额，`update_kb_message` 不支持 agent_steps，因此不能承诺完整恢复所有字段。原会话删除后，读取快照不会重建会话。

---

#### `get_research_task` — 轮询异步任务

**用途**:查询 `submit_deep_research` / `submit_stock_screen` / `submit_notes_report` / `submit_company_roundtable` / `submit_kb_question` / `regenerate_kb_answer`
提交的任务状态与结果。**只能查询当前 API key 自己提交的任务；持久付费任务还须匹配提交时的绑定账号**。修改绑定不转让历史；更换账号应联系服务方撤销旧 key 并重新发 key。此调用计入
data 类配额(rpm/日额度),**不消耗 research 日额度**——放心轮询,但请遵守建议间隔。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `task_id` | string | 是 | — | 提交时返回的任务 ID(UUID) |
| `include_original_native` | bool | 否 | false | 仅原生重新生成任务：显式读取原回答快照，普通轮询省略 |
| `original_native_offset` | int | 否 | 0 | 快照 UTF-8 JSON 的字节偏移；仅 include_original_native=true 可非零。首请求0，后续原样传 next_offset；须为int64非负整数，不能传bool或小数 |

**返回结构要点**(按状态):

| 状态 | 返回 |
|---|---|
| `running` | `{task_id, status: "running", progress: "<当前阶段描述>"}` |
| `done` | `{task_id, status: "done", result: {...}}` |
| `failed` | `{task_id, status: "failed", error: "<原因>"}` |

本版本创建的付费任务还返回 `idem_key` 与 `idempotency_persisted:true`；即使提交时省略或传空键，也可先查历史找到 task_id，再轮询取得生成的 `auto:<UUIDhex>` 恢复键。历史只提供任务定位，恢复提交须向同一工具显式传该键与完整原参数，轮询不会自动重新派发。旧任务可能没有这些字段。

原生任务保留原 task_id 与原生 conversation_id / message_id / generation_id。完成结果可能为部分交付；以返回的 completion（complete / stopped / failed / worker_lost）/ partial 和正文为准，不把部分回答当作完整成功，也不把停止请求当作终态。新回答已部分交付仍计入账号用量。仅轮询原任务，不为等待或观察失败创建新任务。

原生知识库的部分交付结果可保留本轮已收到的可选 `doc_id_mapping` 与证据统计。只核对该结果实际提供的 E 编号；旧服务、历史任务或来源不足时映射仍可能为空。来源映射不表示回答完整、停止成功或已退款，缺少对应项时不能宣称来源已核验。

`include_original_native=true` 仅适用于原重新生成任务且每页仍须匹配原 key、原绑定账号与有效授权。返回 snapshot_only=true；普通轮询不自动返回大快照。该分支保留已存 pending / running / done / failed 状态，不刷新生成状态，不写回网页消息、不重新派发、不触发结算，不能用快照状态断言当前生成已经完成。

完整原快照 JSON ≤262144 bytes 时，offset=0 返回 original_native_snapshot 对象；大对象返回 original_native_snapshot_chunk，包含 total_bytes、snapshot_sha256、chunk_offset、next_offset、encoding:"base64-json-utf8"、data（base64），以及 conversation_id / message_id / recovery_snapshot_id / versions_trimmed。

每页调用计入data配额与请求频率，不消耗research提交额度。每页原始bytes最多262144（base64最多349528字符）。小对象只接受offset=0；offset达到或超过total_bytes返回BadParam，不能用手算偏移跳过终页判断。

读取大快照按以下步骤进行：

1. 首请求 original_native_offset=0，显式 include_original_native=true；核对原任务和恢复标识。
2. 每页将 data 按 base64 解码为 bytes，按 chunk_offset 累积；下一次传原样 next_offset，它是 UTF-8 **字节偏移**，不是字符数。next_offset=null 才是终页。
3. 每页核对同一 conversation_id / message_id / recovery_snapshot_id / snapshot_sha256 / total_bytes。累计字节数必须等于 total_bytes，整体 SHA-256 必须等于 snapshot_sha256；失败就停止，不用不完整材料恢复。
4. 校验通过后才一次 UTF-8 解码并 JSON 解析。不能逐页先解码 UTF-8，分片可能切在中文或 emoji 字节中间，也不能把每页当完整 JSON。

原快照内 content / agent_steps / versions 保留完整原字符串及各字段字节数；versions 非空且合法时再解析其 JSON，不自动修复或丢弃旧数据。大快照不可变 JSON 含原正文、步骤、版本、字节数及原生/恢复标识，不含页外的 versions_trimmed；后者可随任务终态变化，不能参与拼接快照的校验。此读取只提供核对及恢复所需数据，不自动恢复；手动编辑仍受 content / versions 限额，不能经 update_kb_message 恢复 agent_steps。


`done` 时的 `result` 结构:

- 深度研究:保留 `{answer(完整回答 markdown), mode, engine, evidence_count, web_evidence_count, disclaimer}`，新增 `query`(上游问题，可能经过改写)、`created_at`(有效带时区时间，无效时为空串)、`doc_id_mapping`、`meta` 与 `citation_note`。`mode` 回显提交模式；`engine` 回显上游标识，不能单凭它判断引用是否完整；两个 evidence 计数透传上游统计，可能为非零值、0 或 null；它们不代表已交付的可追溯引用数量，不能据此编造来源。`doc_id_mapping` 形如 `{"E1":{"doc_id":"安全文档标识","t0_date":"2026-10-01"}}`，仅接受 E 正整数编号，日期未知时为空串；`meta` 可含非负整数 `latency_ms`、`citable_count` 与 `dropped_uncitable_count`，也可能为空。映射可能为空，不保证每个回答都有可追溯文档；无映射时保留正文原引用标记，不编造标题或链接，并说明引用信息有限。危险路径、存储 URI、签名 URL 与凭据型标识不会透出；历史已完成任务也使用同一结果契约;
- 产业链选股:选股引擎完整结果对象(产业链图谱、候选公司与排名信息)+ `disclaimer`;
- 深度纪要:`{title, markdown, pdf_download_url, pdf_download_expires_at, disclaimer}`(见 `submit_notes_report`)。

研究正文与来源信息应一起使用：

- 保留正文已有的 `[E1]`、`[W1]` 等标记；E 编号可对照 `doc_id_mapping` 中可用的安全文档标识与来源日期（若提供）。来源日期不能自动当作所有相关事实的数据截止日。
- `doc_id_mapping` 是检索证据标识，不是逐条结论的出处核验；不能仅凭映射或 evidence 计数宣称每个事实都已查证。
- W 编号仅指本轮联网补充条目，不代表已定位原始网页、已核实 URL 或可访问链接。未提供对应来源信息时说明限制，不补造网页标题或链接。
- 结合 `citation_note` 使用结果；映射为空、缺少对应项或正文未给标记时如实说明引用信息有限，不替答案补贴来源编号，也不把无法核对的标记说成已验证出处。引用时原文保留 `disclaimer`。
- 核对数字时同时核对主体、期间、单位与分母，近似比例不能扩写为更精确的数值。保留原摘录的“可能”等限定及候选原因；推导须说明条件。来源数字冲突时明确列出差异并待核验，不能仅按报告日期、来源数量或取平均消除冲突。缺少原摘录的抽取摘要及经过清洗的文本不能称为已完成原文核验。

**示例**:

```jsonc
// 调用:get_research_task(task_id="6f9c1e2a-…")
// 返回(done,摘要,取自真实调用):
{
  "task_id": "6f9c1e2a-…",
  "status": "done",
  "result": {
    "answer": "# 一、景气阶段判断\n\n当前存储芯片行业正处于…(完整研究回答 markdown)",
    "mode": "flash",
    "engine": "agentic",
    "evidence_count": 0,
    "web_evidence_count": 0,
    "disclaimer": "本内容由 ADAMAS 模型生成,仅供研究参考,不构成任何投资建议;据此操作风险自担。引用时须保留本声明。"
  }
}
```

---

#### `list_my_research_tasks` — 任务历史与回执恢复

**用途**:列出当前 API key 的已落库任务摘要。提交后没有收到 task_id，先检索历史确认任务是否已接收，避免重复提交；它计入 data 日额度，不消耗 research 提交额度。

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `limit` | int | 10 | 每页 1–50 条 |
| `status` | string \| null | `null`（可省略） | 不筛选，或 `pending` / `running` / `done` / `failed` |
| `kind` | string \| null | `null`（可省略） | 不筛选，或 `deep_research` / `notes_report` / `stock_screen` / `company_roundtable` / `native_kb` |
| `cursor` | string | 空串 | 下一页使用上页 `next_cursor`，保持原 status / kind |

不筛选时省略 `status` / `kind` 或传 `null`，不要传空字符串；`cursor` 的默认值仍为空字符串。

**返回**:`tasks[]`(含 `task_id`、`kind`、`status`、`progress`、失败时 `error`、`error_class` 与 `created_at` / `started_at` / `finished_at`)、`count`、`has_more`、`next_cursor`(末页 null)及 `meta.note`。按创建时间与 task_id 倒序，游标绑定当前 key、绑定账号和过滤条件；换 key、账号或条件会拒绝。旧版本游标失效时省略 cursor 从第一页重新获取。历史不包含问题、研究正文或完整结果，也不主动同步上游状态；找到 task_id 后用 `get_research_task` 获取当前状态和结果。它不能恢复其他 key 的任务。

研究结果的 `meta` 可选带 `citable_count`（本轮作答映射的本地证据编号数）与 `dropped_uncitable_count`（进入作答前因缺少安全来源而排除的检索项数），仅返回非负整数。旧结果可缺省；两者不保证相加等于检索总量，统计不能代替逐条事实核验。

### 3.3 网页知识库与热点历史（data 配额）

以下入口属于 Standard 的 data 配额，但含编辑、删除、公开分享等写操作，
**data 类不等于只读**。网页知识库入口要求 key 已绑定本人有效账号，且该账号已开通
知识库能力；MCP 档位不能替代网页账号权限。无会话时返回正常空列表。游标为不透明字符串（≤1024字符），原样传回；更换账号、会话或筛选时重新取首页。

网页 `conversation_id` / `message_id` 是正整数，与 MCP 研究的 UUID `task_id`
以及深研 `session_id` 分别管理。`submit_deep_research` 不自动创建网页会话；
新建或续问使用 research 类 `submit_kb_question`，重新生成使用 `regenerate_kb_answer`；本节管理工具本身不提交生成。

#### `list_kb_conversations` — 列出本人的网页知识库会话

参数 `limit` 默认 20、范围 1–100；`cursor` 默认空串，后续原样使用 `next_cursor`。
返回 `conversations[]`，按更新时间倒序分页。只读取本人的网页会话，不提交研究。

#### `get_kb_conversation` — 读取网页会话消息

必填 `conversation_id` 来自会话列表；`limit` 默认 20、范围 1–100；`cursor`
默认空串。按时间顺序返回 `messages[]`，保留完整正文；`has_more=true` 时用
`next_cursor` 继续。消息 `id` 可用于后续编辑、分享或停止生成，不能当成研究 task_id。含原生生成的消息可带当前最新 generation_id，停止时应使用本轮标识。

#### `delete_kb_conversation` — 删除网页会话

必填 `conversation_id`；`confirm_delete` 默认 false，只有用户明确要求删除时才传
`true`。软删除本人会话及消息，不删除或取消 MCP 研究任务，不请求退款。
有活动生成时拒绝删除，先请求停止并确认终态。删除不抹去独立研究回执或原回答恢复快照，读取快照不会恢复已删除的会话。
**已经公开的分享快照会独立保留**：删除前用 `manage_kb_shares` 列出分享并按需撤销。

#### `update_kb_message` — 编辑网页知识库消息

必填 `message_id` 与 `changes`。`changes` 至少提供 `content`（正文，≤400000个Unicode字符）
或 `versions`（正文字符串数组）。`changes.versions` 最多20项，每项≤399996个Unicode字符；
完整数组按 `json.dumps(versions, ensure_ascii=False)` 默认格式序列化后≤400000个Unicode字符，
含括号、引号、转义、逗号和空格。非ASCII字符不转义，元素之间用逗号加一个空格分隔。
这些字段限制同时生效，仍须满足完整 UTF-8 JSON-RPC 请求体的 1 MiB 上限；
字段总字符数合法不保证最终请求字节数合法。生成中的消息必须先请求停止并读取确认终态。
编辑不重新生成、不运行研究，也不补造原回答来源；不能编辑 agent_steps，不能声称通过它完整恢复原回答所有字段。

#### `share_kb_content` — 创建公开分享快照

必填 `target:"conversation"|"message"` 与 `resource_id`（相应会话或助手消息的正整数ID）；
`make_public` 默认 false。**任何持有链接的人均可免登录阅读**，只有用户明确要求
公开分享时才传 `make_public:true`。返回 30 天有效快照的 `share_url` 与 `expires_at`。
每次调用都会创建新链接，不能盲目自动重放；超时先查 `manage_kb_shares` 核对。

#### `manage_kb_shares` — 查询或撤销分享

参数 `action:"list"|"revoke"`、`resource_id`。`list` 时 ID 是网页会话 ID，返回尚未
过期的 `shares[]`；`revoke` 时 ID 是列表返回的分享 ID，使对应链接立即失效。
它不会新建分享。已删除会话的残留分享也可按返回的分享 ID 撤销。

基于检索材料的知识库回答会先核对材料与结论，再显示通过核对的正文，首字等待可能延长。等待期间按原 `task_id` 查询，不因暂时没有正文另起新任务。核对不能确认时不会当作完整结果交付；是否有新回答及如何结算，以原任务的终态、`completion` / `partial` 和服务端结算结果为准。可在等待中按原轮请求停止，也可停止尚在交付的正文；收到停止请求回执不证明正在生成的上游请求已结束。

MCP 提问、重新生成和深度研究按本轮材料组织答复，区分原摘录、条件计算和待核验口径。近似数保留原精度，候选原因保留“可能”等限定；未建立的年份、期间和分母不由其他指标或金额计算补齐。计算会列明假设，不能以结果接近认证同一统计口径。

#### `stop_kb_generation` — 按轮次请求停止知识库生成

参数 `message_id` 为助手消息正整数 ID；可选 `generation_id` 为本次生成 UUID，默认空串。原生 MCP 任务总是传回执的原 generation_id，不能拿旧轮次停止后来的重新生成。旧网页流可省略此字段，仍仅按旧流句柄处理。

指定原轮停止被旧服务拒绝时，保留原 generation_id 并查询原任务；不要省略 generation_id 降级为消息级停止，也不要换成后续轮次的标识。等待服务更新或联系支持，拒绝不证明该轮已停止。

- `cancel_requested`：已请求停止；仍需查询原任务或消息确认终态。
- `not_running`：该轮已经结束或不在运行，不会转而停止后续轮次。
- `not_cancellable_here`：当前服务没有可取消句柄；不能解释为已停止。

停止不等于退款；已有部分新回答时保留为新版本并计入用量，没有新回答的重新生成由服务端原样回退。它不支持普通深研 task_id 或通用 AI 异步任务取消，不请求积分退款。关闭客户端也不能证明任务已停止。确认终态之前保留原任务及原幂等键，不另起任务绕过等待。

#### `get_hot_notes` — 检索热点纪要历史与正文

参数 `date` 默认空串（可传 `YYYY-MM-DD`）、`cursor` 默认空串、`limit` 默认 50
且范围 1–100、`note_id` 默认 0。无 note_id 时按日期/编号倒序返回 `items[]`
与 `next_cursor`，继续翻页时保留原日期；空游标表示末页。

`note_id>0` 时读取相应纪要正文 `paragraphs[]`，不可同时传日期或游标。
这批已发布热点纪要与 `get_info_feed` 的当前市场摘要、`submit_notes_report`
新生成的研究纪要是不同数据，不把历史内容写成实时新闻。

## 4. 异步任务模式(research 类完整生命周期)

```
submit_deep_research / submit_stock_screen / submit_notes_report / submit_company_roundtable / submit_kb_question / regenerate_kb_answer
        │  秒级返回原任务回执 task_id(受理状态可能待确认)
        ▼
get_research_task(task_id) ──► running(带 progress 阶段描述)──► 继续轮询
        │
        ├──► done   ──► result(含 disclaimer,引用原文保留)
        └──► failed ──► error + error_class + recovery(确认终态与原因后处理)
```

**耗时预期与轮询间隔**:

| 任务 | mode | 耗时预期 | 建议轮询间隔 |
|---|---|---|---|
| 深度研究 | `flash` | 约 1–2 分钟 | ≥30 秒 |
| 深度研究 | `auto` | 约 2–5 分钟 | ≥30 秒 |
| 深度研究 | `plus` | 约 5–10 分钟 | ≥30 秒 |
| 深度研究 | `pro` | 约 8–12 分钟 | ≥30 秒 |
| 产业链量化选股 | — | 约 3–8 分钟 | ≥60 秒 |
| 深度纪要报告 | — | 约 8–15 分钟 | ≥60 秒 |
| 多公司报告横向研究 | — | 按公司与材料规模变化，以回执指引为准 | 按 next_step，建议≥30 秒 |
| 原生知识库提问/重新生成 | auto / flash / plus / pro | 以实际回执指引为准 | 按 next_step，间隔≥30 秒 |

**实践建议**:

- 提交返回中的 `next_step` 字段已给出轮询指引,agent 直接照做即可;
- 提交回执丢失、超时、网络断开或 progress 提示受理待确认时，先查 `list_my_research_tasks` 找回 task_id，再轮询 `get_research_task` 取回状态与恢复键；网络断开不等于任务取消，也不等于已退款。需要恢复提交时，显式传返回的 idem_key 与完整原参数；继续传空键仍会新建意图，轮询不会自动重新派发;
- 等待期间不要空转:可先用 data 类工具取相关产业/标的的客观数据、起草报告框架(预置 prompts 即按此编排,见第 7 节);
- 超时结算不能从等待时长自行推断；旧版遗留任务或确认未派发的过期意图仍以原 task_id 返回的终态、错误与 `recovery` 为准。新版请求已经发出但受理未知时，不会仅因超过耗时预期或 1 小时就判失败、退款；保留原任务，不换键重投。确认原任务终态后，明确决定再次生成才使用新 idem_key；这是新任务，会正常消耗提交额度;
- 轮询到 `done` / `failed` 后状态即为终态,结果已落库,可重复查询;
- `task_id` 与 API key 绑定,换 key 查不到。

## 5. 配额与限流

每个 API key 的默认配额(可按商务约定单独调整):

| 维度 | 默认值 | 超限表现 |
|---|---|---|
| 请求频率(rpm) | 60 次/分钟(令牌桶) | **HTTP 429** + `Retry-After` 头 + JSON `{error, retry_after_seconds}` |
| data 类日额度 | 2000 次/日 | `error: "数据类工具今日额度(2000)已用完"` + `retry_after_seconds`(到次日 0 点的秒数) |
| research 类日额度 | 20 次提交/日 | `error: "研究类工具今日额度(20)已用完"` + `retry_after_seconds`(到次日 0 点的秒数) |
| 单 key 研究并发 | 每个 key 同时 1 个在跑 | `error: "你的上一个研究任务还在进行中(每个 key 同时只允许一个),请等它完成后再提交"` + `retry_after_seconds: 60` |
| 深度研究全局并发 | 全部 key 合计 2 个在跑 | `error: "深度研究并发已满,请稍后重试"` + `retry_after_seconds: 120` |
| 产业链选股全局并发 | 全部 key 合计 1 个在跑 | `error: "选股任务并发已满,请稍后重试"` + `retry_after_seconds: 180` |
| 深度纪要全局并发 | 全部 key 合计 1 个在跑 | `error: "纪要生成并发已满,请稍后重试"` + `retry_after_seconds: 300` |
| research 类账号用量 | 按绑定账号的开通范围计 | `error: "今日使用已达上限，请联系工作人员"` |

### research 类工具与账号用量

research 六个提交工具(`submit_deep_research` / `submit_stock_screen` /
`submit_notes_report` / `submit_company_roundtable` / `submit_kb_question` / `regenerate_kb_answer`)
除上表的 key 日额度外,**还消耗 API key 所绑定账号的使用额度**,与该账号在网页端
的用量算在一起。新业务会运行对应的研究或选股流程；同键同参重放返回原任务，不重复扣本次账号用量。因此:

- **API key 必须绑定账号**才能调用 research 类工具。未绑定时返回
  `error: "该 API key 未绑定用户,无法使用研究类工具;请联系 ADAMAS 为 key 绑定账号"`
  ——部分公开 data 查询不受此限制；网页知识库与热点历史仍须绑定有效账号，知识库另须开通网页能力;
- **`submit_deep_research`、`submit_kb_question`、`regenerate_kb_answer` 选 `mode="pro"` 时用量按 2 倍计**(与网页端知识库的 Pro 单次问答模式一致，不是订阅档位),
  其余档位(`auto`/`flash`/`plus`)按 1 倍;
- **已确认失败且没有新回答交付的原生任务按服务端结算逻辑退回本次账号用量及研究提交额度**；原生生成的部分新回答也计入用量，重新生成回退的原答案不算本轮新交付。客户端断开本身不代表任务失败或退款，恢复 task_id 后查询终态。**成功产出的任务不退**——包括你觉得结果不理想的情况;
- 账号额度用尽时返回 `error: "今日使用已达上限，请联系工作人员"`,
  与 key 日额度是两套独立限制,任一撞上都会被拒;
- 计费服务短暂不可用时 research 类工具会**拒绝提交**(返回
  `error: "计费服务暂时不可用,请稍后重试"` + `retry_after_seconds`),
  而不是免费放行；等待不等于安全重放授权，按 `recovery` 处理，结果未知先查原任务。

说明:

- **每个 key 同时只允许 1 个 research 任务在跑**；未完成前重复提交会直接返回退避 60 秒。
- research 日额度只在**提交**时消耗;`get_research_task` 轮询走 data 类配额;
- research 全局并发闸是服务级保护(受上游算力约束)，与你的用量无关也可能撞到；队列按 `recovery` 处理。提交结果不明先查历史，不把所有失败都当成可安全重试;
- **频率(rpm)按每个 HTTP 请求计**,包含 `initialize`、`tools/list`、`prompts/*`、`ping` 等协议请求,不只是工具调用。超限返回 **HTTP 429**(带 `Retry-After` 头);
- **日额度按工具调用计**，`get_my_quota` 豁免日扣减；超限以工具返回的 `error` / `error_class` / `recovery` / `retry_after_seconds` 呈现，MCP `isError=true`。日额度的等待时间是**到次日 0 点(北京时间)的秒数**，不要每小时空试;
- **日额度落库,服务重启/更新不会重置**;并发超限同样按 `retry_after_seconds` 退避,密集重试只会持续消耗 rpm;
- 服务对已解析的 `tools/call` 只做 best-effort 单次计量写入尝试;计量失败不影响
  主请求,不保证持久化或 exactly-once。成功写入的用量按 key 查看,如需提额请联系 ADAMAS。

## 6. 数据口径与合规(重要)

集成方必须遵守以下约定:

1. **一切数值以返回中的 `as_of` 为准**。行情为每交易日盘后(约 16–17 点)人工导入,存在 T+0 晚间前的滞后:交易日当天下午调用可能拿到的仍是上一交易日数据——这不是故障。判断时效请对照 `list_capabilities().freshness`,并在你的产出物中把 `as_of` 标注给最终读者(如「ADAMAS 数据,截至 2026-07-23」)。全球宏观报告单独以 `latest_date` / `report_date` 为准,成文时同样必须标注。
2. **免责声明必须原文保留**:research 类结果及含模型观点的 data 类返回(`get_model_picks` / `get_industry_scores` / `get_company_tracking` / `get_global_macro`)均带 `disclaimer` 字段(全球宏观放在 `meta.disclaimer`)。你的 agent 在引用这些内容产出报告/回答时,**必须一字不改地保留该声明**;
3. **输出内容不构成投资建议**:所有数据与观点仅供研究参考,不构成对任何人的投资建议,据此操作风险自担。将本服务能力集成到面向终端用户的产品时,合规责任由集成方承担;
4. 建议在成文时区分三种内容:①ADAMAS 客观数据(标 `as_of`)②ADAMAS 模型观点(深度研究/选股/景气度打分,注明来源)③你自己的推断与综合。
5. **全球宏观地区与打分口径不得改写**:`China-Taiwan` 只是
   `regions` 中的中国台湾地区,不计入国家数;当 `score_ready=false` 时,
   `score=null` 表示周期打分尚未上线,不得臆造分数或排名。

## 7. 预置 Prompts 与 Agent Skill

### 7.1 MCP Prompts(随 server 下发)

服务端预置 2 个 prompts,内置了「怎么用好这些工具」的调用顺序与引用规范。支持 MCP prompts 的客户端(如 Claude Code 中输入 `/` 可见,形如 `/mcp__adamas__industry_brief`)可直接选用:

| Prompt | 参数 | 产出 |
|---|---|---|
| `industry_brief`(行业跟踪简报) | `industry` 产业名 | 景气度 + 六维趋势 + 历史快照 + 全市场量化选股结果中的相关代表标的 → 成稿报告 PDF 与公司基本面跟踪要点,成文标 as_of、保留 disclaimer |
| `deep_research_report`(深度研究报告) | `topic` 研究主题 | 提交 plus 档深度研究 + 等待期间取产业数据与最新量化选股结果 → 综合成文(研究结论注明来自 ADAMAS 研究引擎 + 数据佐证标 as_of + 交叉验证) |

不支持 prompts 的客户端,可把上述编排写进你自己的系统提示词,方法论同源于第 7.2 节的 Skill。

### 7.2 WorkBuddy / OpenClaw / Kimi Code Skill 包

Skill 包与本文档一起发布在**公开接入仓库** <https://github.com/felixhjh-2/adamas-mcp-connect>
(路径 `plugins/adamas-research-report/skills/adamas-research-report/`),内容为「ADAMAS 投研报告」方法论:先看地图再取数、代码先解析、全球宏观先拉覆盖全景再读正文、数据与观点分开取分开写、限流退避、成文规范(日期标注、三类内容区分、disclaimer 原文保留、六维趋势符号含义)以及行业跟踪、公司横向研究、历史资料管理等常用剧本。

安装方式:

- **WorkBuddy**:先接入 ADAMAS MCP 连接器(见 2.1),再下载上述仓库,把 Skill 目录作为技能导入(入口一般在 技能/Skill 管理 → 导入本地技能包);
- **Kimi Code**:把 Skill 目录复制到用户级
  `~/.kimi-code/skills/adamas-research-report/` 或项目级
  `.kimi-code/skills/adamas-research-report/`,新开会话后可用
  `/skill:adamas-research-report` 显式调用。目录规则见
  [Kimi Code 官方 Agent Skills 文档](https://www.kimi.com/code/docs/kimi-code-cli/customization/skills.html);
- **Claude Code**:插件一步装齐(MCP 连接 + Skill,key 走环境变量 `ADAMAS_API_KEY`):
  会话内 `/plugin marketplace add felixhjh-2/adamas-mcp-connect` → `/plugin install adamas-research-report@adamas`;
- **OpenClaw / 其他支持 Agent Skills 的框架**:把 Skill 目录放入框架的 skills 目录即可(触发条件与用法在 `SKILL.md` frontmatter 中)。

Skill 与 MCP prompts 方法论同源:装了 Skill 的 agent 会主动按 ADAMAS 推荐的顺序调用工具并遵守成文规范,显著降低集成后的提示词调试成本。

## 8. FAQ / 故障排查

**Q:HTTP 401,提示「缺少 API key」或「API key 无效或已禁用」?**
检查 `Authorization` 头是否为 `Bearer <your-api-key>` 格式(注意 `Bearer` 后有空格)、key 是否复制完整(以 `adamas_` 开头)。仍失败则 key 可能已被禁用或未开通,联系 ADAMAS 确认。

**Q:HTTP 401,提示「API key 已过期」?**
你的 key 设有有效期且已到期。联系 ADAMAS 续期即可,续期立即生效,无需换 key。

**Q:ChatGPT / Claude 等 OAuth 注册提示 `redirect_uri host not allowed`，或授权后跳不回客户端?**
确认客户端回调主机位于 2.6 的精确白名单，并删除旧连接后重新创建，让客户端重新做动态注册。
ChatGPT 每个 App 会生成不同 callback 路径，这是正常的；服务端按 `chatgpt.com` 主机放行，
不要求固定路径。若授权页提示未登录，请先登录 `www.adamas-research.com` 再重试。

**Q:Claude Code 添加后仍显示 401，或没有出现 OAuth 登录?**
先检查现有 `adamas` 配置。OAuth 命令必须省略 `--header` / `Authorization`；如果此前建过
Bearer 连接，删除旧连接后按 2.3 节的 OAuth 命令重新添加，再运行
`claude mcp login adamas` 或在 `/mcp` 中 Authenticate。本仓库插件的内置连接仍是
`ADAMAS_API_KEY` Bearer 方案；使用插件连接时必须注入该环境变量。

**Q:HTTP 421(Misdirected Request)?**
服务端开启了 DNS-rebinding 保护,只接受 Host 白名单内的请求(`www.adamas-research.com` 等)。直连官方端点不会遇到此问题;若你在自建网关/反向代理后面转发请求,必须**透传原始 Host 头**(如 nginx `proxy_set_header Host www.adamas-research.com;`),或联系 ADAMAS 把你的域名加入白名单。

**Q:返回里带 `error` 和 `retry_after_seconds`(额度/并发超限)?**
这是结构化的业务失败信号:`CallToolResult.isError=true`，内容保留 `error` 并新增 `error_class` / `recovery`。先按 recovery 判断是改输入、检查额度/权限、查任务历史还是等待；只有 `retry_safe=true` 才自动重放。日额度类等待时间指向**次日 0 点(北京时间)**，当日不必再试。

**Q:收到 HTTP 429?**
频率超限(每分钟调用数)走 HTTP 429,响应带标准 `Retry-After` 头和 `retry_after_seconds` 字段,按其中任一等待后重试即可。注意频率是按**每个 HTTP 请求**计的,连接握手、列工具等协议请求也计入。

**Q:字段字符数没有超限，为什么仍收到 HTTP 413?**
`POST /mcp` 的完整 UTF-8 JSON-RPC 请求体（协议字段及全部参数）最多 **1 MiB（1048576 bytes）**；可查看 `list_capabilities().transport.request_limits`。
字段字符上限不等于完整请求字节上限，中文、emoji、JSON 转义和空白都计入实际传输字节；多个字段和 history 也共同占用同一请求体上限。
超限返回 HTTP 413，本次请求未进入工具业务；不能据此推断此前受理状态未知的提交未被受理，先核对原任务历史或原资源，不能据此断言旧任务取消或退款。
不自动截断文本、丢弃 history 或 versions，也不换键重投写入或收费操作。大文本可用网页编辑，或由用户明确缩小输入范围后再操作。

**Q:编辑消息的 versions 每项都没有超限，请求也低于 1 MiB，为什么仍返回 BadParam?**
每项≤399996个Unicode字符只是单项上限；完整数组还须按 `json.dumps(versions, ensure_ascii=False)`
默认格式序列化后≤400000个Unicode字符，包含框架、转义及元素之间的逗号和空格。
例如两项各200000个ASCII字符，序列化数组有400008个字符，仍会被拒绝。
按 `update_kb_message` 的全部字段限制和完整请求字节上限一起检查，不自动截断或丢版本来绕过限制。

**Q:任务 `failed`,错误是「任务超时未完成(服务可能重启过),请重新提交」?**
这条错误对应旧版遗留任务的 1 小时 TTL 处理，仅在原 task_id 已实际返回 `failed` 终态时适用，不能用来判断新版受理未知的任务。新版确认尚未派发的意图若安全过期，也以原任务返回的错误与 `recovery` 为准；已经发出请求但受理未知的任务不会仅因超过 1 小时就判失败或退款。先确认原任务终态及恢复指引，明确决定再次生成才发起新业务，不自动重投；新业务会正常消耗 research 提交额度。

**Q:调用工具时返回「服务即将更新维护,暂停接收新任务,请几分钟后重试」?**
服务处于更新窗口(排空中)，会拒绝尚未接纳的新工具调用，已接纳的调用会继续跑完。这种明确拒绝与已经向研究引擎发出请求、受理状态未知不同；维护错误不能证明此前的未知提交已取消或未发生。
`retry_after_seconds`(300 秒)只是等待建议，只有 `recovery.retry_safe=true` 才自动重放。付费提交返回的 `recovery.action="check_task_history"`、`retry_safe=false` 要求先查历史或原 task_id；保留原 idem_key 与完整参数，受理仍未知或无法唯一恢复时停止并联系支持，不换键或继续传空键重投。

**Q:研究结果里 `evidence_count` 是 0?**
这是上游返回的统计值，也可能为非零值或 null；0 或 null 不证明没有检索证据，非零值也不证明已有可追溯引用。应检查正文及 `citation_note` / `doc_id_mapping`，保留已有 E/W 标记并说明无法核对的部分。映射可能为空，不得据此补造编号、文档标题或链接；W 条目也不等于已定位或已核实的原始网页。`mode` 回显提交模式。

**Q:轮询 `get_research_task` 返回「引擎状态暂不可查，请稍后查询原任务」?**
这表示当前无法确认引擎状态；返回 `running` 不证明任务已受理或正在执行。按正常间隔继续查询原 task_id，缺少 ID 时先用 `list_my_research_tasks` 恢复；无法唯一恢复时停止并联系支持。新版请求可能已经发出但受理未知，即使超过耗时预期或 1 小时，也不能自行判失败、推断退款或换键重投；保持原 UUID、原幂等键和完整参数，按原任务的状态与 `recovery` 处理，不套用旧版 TTL 规则。

**Q:`get_company_tracking` 返回了目录但 `content` 为空、带 `content_error`?**
`meta.content_status="unavailable"` 表示全文未交付，目录可继续使用；这是 `isError=true` 的部分结果。检查 `error_class` 与 `recovery`：`S3Misconfigured` 需联系支持修复配置，临时 `Upstream` 按指引等待。`truncated` 则表示只交付了部分正文，不能当成全文。

**Q:交易日下午调用,行情相关 `as_of` 还是昨天?**
正常现象:行情为盘后 16–17 点人工导入(见第 6 节),当天数据在晚间前可能尚未就绪。以 `freshness` / `as_of` 为准。

**Q:`get_global_macro` 里 `score_ready=false`、`score=null`,是不是分数为 0?**
不是。这表示宏观周期打分模型尚未上线,不得当作 0 分,也不得自行生成
分数、排名或颜色等级。直接依报告正文做定性分析,并标注 `report_date`。

**Q:为什么 `China-Taiwan` 不在 `countries` 里?**
它代表中国台湾地区,按契约只在 `regions` 中返回,不计入覆盖国家数。
需要读它的报告时,仍可把返回的 `country_key` 值 `China-Taiwan` 传给
`get_global_macro(country=...)`;对外展示应使用返回的 `country_name`。

---

其他问题、申请 API key、提额、加 Host 白名单:联系 ADAMAS 团队。

客户端可能缓存 tools/list；升级后若看不到新工具，先刷新工具列表或断开后重新连接，再检查当前 key 的授权发现。接入材料 2.6.5 与服务 contract_version `2026-10-14.2` 是不同版本标识。
