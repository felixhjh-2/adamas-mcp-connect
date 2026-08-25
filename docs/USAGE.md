# ADAMAS MCP 使用文档

> 面向外部集成方。读完本文即可把 ADAMAS 投研能力接进你自己的 agent / IDE / 办公工具。

## 1. 概述

ADAMAS MCP 是 ADAMAS 金融投研平台的对外能力分发服务,以
**remote MCP server(streamable HTTP)** 形态提供。它适配能配置自定义
remote MCP endpoint 与 `Authorization: Bearer` 请求头的客户端
(WorkBuddy、Claude Code、Cursor、Codex、自建 agent 框架等)。

> **接入前提**:当前服务未实现 MCP OAuth discovery / 自动授权,
> 需手工配置端点和 Bearer key。如果你的客户端版本不能为 remote MCP
> 连接设置自定义 HTTP header,就不能直接接入当前服务。

它对外提供八类投研能力:

| 能力域 | 说明 |
|---|---|
| 产业景气度 | 约 190 个产业的景气度打分、六维趋势、跟踪摘要与历史快照 |
| 产业报告 | 边际跟踪报告与完整深度报告的 PDF 下载(成稿报告直接给最终用户) |
| 产业关联图谱 | 约 190 个产业节点 + 产业链传导关系边(方向/强度/时滞),支持传导链推演 |
| 公司跟踪 | 约 2400 家公司的跟踪报告全文(markdown,含历史期)与历史目录 |
| 全球宏观 | 分经济体的九维度报告覆盖、最新正文与历史期对比 |
| 每日信息流 | 多源聚合后二次加工的当日市场要闻打分摘要(晨会/盘前场景) |
| 模型与产业链选股 | 最新模型排名(秒级只读)与产业链量化选股任务(异步) |
| 深度研究与纪要 | 深度研究问答、深度纪要报告生成(异步任务) |

- **端点**:`https://www.adamas-research.com/mcp`
- **传输**:MCP streamable HTTP(无状态,支持断线重连后重新调用)
- **认证**:每个请求携带 HTTP 头 `Authorization: Bearer <your-api-key>`,API key 向 ADAMAS 申请获取(key 明文只在发放时出现一次,请妥善保管)
- **内容**:本公开主文档对应 Standard 档,**15 个工具**(12 个 data 类 + 3 个 research 提交工具)+ 2 个预置 prompts + 1 个 WorkBuddy/OpenClaw Skill 包。Standard 包含模型选股排名、产业链量化选股与全球宏观入口。本公开文档只描述 Standard 契约。

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

### 2.2 Claude Code

```bash
claude mcp add adamas --transport http https://www.adamas-research.com/mcp \
  --header "Authorization: Bearer <your-api-key>"
```

验证:`claude mcp list` 应显示 adamas 已连接;会话内 `/mcp` 可查看工具清单。

### 2.3 Codex

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

### 2.4 Cursor

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

### 2.5 Claude Desktop

ADAMAS 当前的自定义 Bearer 认证不能直接配置进 Claude Desktop 的 remote
connector。Claude Desktop 的 remote MCP 需从 Settings → Connectors 添加,
当前界面提供免认证或 OAuth 流程;
`claude_desktop_config.json` 只配本地 server,不会按上面 Cursor 的 JSON 连接
remote HTTP server。由于 ADAMAS MCP 目前是自定义 Bearer header 且尚未实现
OAuth,请改用 Claude Code、Cursor、Codex 或 WorkBuddy。

### 2.6 自建 agent(Python,官方 mcp SDK)

先安装已验证的新客户端 API 版本:

```bash
python -m pip install "mcp>=1.28.1,<2"
```

```python
import asyncio, json
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

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

            # 3) 产业景气度 + 当日高分信息流
            ind = parse(await session.call_tool("get_industry_scores", {"industry": "存储"}))
            print(ind["industries"][0]["name"], ind["industries"][0]["score"])
            feed = parse(await session.call_tool("get_info_feed", {"limit": 3}))
            print([it["title"] for it in feed.get("items", [])])

asyncio.run(main())
```

工具返回同时携带 structured output(`result.structuredContent`,JSON dict)与等价的 JSON 文本(TextContent);上例的 `parse` 两者都兼容,建议照抄。agent 类客户端(Claude Code / WorkBuddy / Cursor 等)无需关心,模型直接读 JSON。

### 2.7 接入后的第一次调用(约定)

1. **先调 `list_capabilities`**:拿覆盖范围与各数据域新鲜度(`freshness`),行情为交易日盘后导入,别把旧数据当今天的;
2. **标的名可先解析**:用 `search_assets` 把公司名/代码解析成标准信息(行业分类/市场风格属性);
3. **所有数值以返回中的 `as_of` 为准**;
4. **超限时按 `retry_after_seconds` 退避**,不要密集重试。
5. **全球宏观先无参调用** `get_global_macro()`:从返回的覆盖全景取
   `country_key`、九维度及最新报告日期,再按需取正文。

## 3. 工具参考

通用约定:

- 所有工具返回 JSON dict。业务层错误(参数错误、未找到、配额超限等)会返回 `{"error": "<原因>"}` 并把 MCP `CallToolResult.isError` 标为 `true`;可退避的错误额外带 `retry_after_seconds` 字段。它们不是 HTTP/传输异常,SDK 通常仍会返回 `CallToolResult`,因此你的 agent 应同时处理 `isError` 和 JSON 中的 `error` 键;
- 数据类返回带 `meta` 字段(口径说明,观点相关的还含 `disclaimer`),数值带各自的 `as_of`(数据截止日);全球宏观报告以 `latest_date` / `report_date` 标日期;
- 参数中的日期一律 `YYYY-MM-DD`;返回中的 `as_of` / `report_date` / 序列日期也是 `YYYY-MM-DD`,仅产业跟踪的 `summary_as_of` 与 `score_history[].date` 为带时区的完整时间戳(如 `2026-07-20 16:06:22+00:00`)。

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
  "freshness": {
    "model_picks_as_of": "2026-07-23",
    "company_reports_latest": "2026-07-24"
  },
  "meta": {"note": "freshness 即各数据域的截止日;所有数值以返回中的 as_of 为准"}
}
```

---

#### `search_assets` — 资产模糊搜索

**用途**:按名称或代码模糊搜索资产,返回 `asset_code`(其他工具的输入主键)与行业分类、市场/风格属性。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `query` | string | 是 | — | 名称或代码片段,如 `"紫金"`、`"601899"` |
| `limit` | int | 否 | 10 | 返回条数,合法范围 1–50;越界为参数错误 |

**返回结构要点**:`matches[]`,每条含 `asset_code`、`asset_name`、`asset_class_l1`、`asset_class_l2`、`market_attribute`、`style_attribute`。排序规则:代码前缀命中 > 名称全等 > 名称短者优先。

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

#### `get_model_picks` — 最新一期模型选股排名

**用途**:查询已发布的最新一期模型选股结果(不触发选股流程,秒级返回),
含总分、百分位、预期收益及市场·风格·宏观分项,可按 L1 行业过滤。
**非投资建议,引用需保留 `disclaimer`。**

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
    "note": "最新一期模型打分排名(纯量化,非投资建议);rank 越小越靠前",
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

**返回结构要点**:`industries[]`,每条含 `name`、`sector`、`score`、`trends`(六个维度,值为方向符号文本:`↗` 改善 / `→` 持平 / `↘` 恶化)、`tracking_summary`(最新跟踪摘要)、`summary_as_of`;`include_history=true` 时另含 `score_history[]`(`{date, score}`)。未匹配到产业时返回 error,并在 `available_industries` 里附上**全部可选产业名**,照着改一次即可命中。

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
| `company` | string | 是 | — | 公司名,支持模糊匹配 |
| `include_content` | bool | 否 | true | 是否返回全文;false 时只返回目录 |
| `report_date` | string | 否 | 最新一期 | 取历史期全文(`YYYY-MM-DD`,从 `history` 目录中选;传错会返回可选日期表) |

**返回结构要点**:`company`、`latest_report_date`、`history[]`(`{report_date, company}`)、`content`(最新一期全文 markdown)、`meta`(note + `disclaimer`)。未找到时返回 error,并在 `did_you_mean` 里给出相近的公司名(按输入前两字宽松匹配),照着改一次通常就能命中。报告存储暂不可用时 `content` 为空串并附 `content_error` 说明(目录仍可用)。

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
    "note": "ADAMAS 公司跟踪体系报告;content 为最新一期全文 markdown",
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
| `names` | string[] | 是 | — | 公司名列表,**一次最多 100 家**(支持模糊匹配);超过请分批 |

**返回结构要点**:`covered[]`(`{asked 你传的名字, company_name 库中标准名, latest_report_date, periods 历史期数}`)、`not_covered[]`(没覆盖的原样回显)、`summary`(`{asked, covered, not_covered}`)、`meta.note`。取全文时请用 `covered[].company_name`(库中标准名)去调 `get_company_tracking`。

**示例**:

```jsonc
// 调用:check_company_coverage(names=["贵州茅台", "宁德时代", "某不存在公司XYZ"])
// 返回(取自真实调用):
{
  "covered": [
    {"asked": "贵州茅台", "company_name": "贵州茅台", "latest_report_date": "2026-08-05", "periods": 5},
    {"asked": "宁德时代", "company_name": "宁德时代", "latest_report_date": "2026-08-07", "periods": 5}
  ],
  "not_covered": ["某不存在公司XYZ"],
  "summary": {"asked": 3, "covered": 2, "not_covered": 1},
  "meta": {"note": "covered 里的 company_name 是库中的标准名,取全文请用 get_company_tracking(company=该标准名)"}
}
```

---

#### `get_industry_report` — 产业报告 PDF

**用途**:取产业的**边际跟踪报告**(每期更新)与**完整深度报告**的 PDF 下载链接。适合把成稿报告直接交付给最终用户阅读。

**参数**:`industry`(必填,支持模糊匹配,最多返回 5 个产业)。

**返回结构要点**:`industries[]`,每条含 `name`、`sector`、`tracking_report_pdf_url`(边际跟踪报告)、`full_report_pdf_url`(完整报告)、`updated_at`。**下载链接 10 分钟有效**,过期重新调用即可;无报告的产业带 `note` 说明。含 `disclaimer`。

---

#### `get_industry_graph` — 产业关联图谱

**用途**:产业节点(景气打分 + 六维方向信号)与产业链**传导关系边**(方向 sign / 强度 strength / 时滞 delay_ticks / 传导通道 channel)。适合回答"上游 A 涨价会传导到谁、多快、多强"这类传导链推演问题。

**参数**:

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sector` | string | 否 | 按板块过滤:`tech` / `cycle` / `consumer` / `pharma` |
| `node` | string | 否 | 按产业名称模糊过滤,只返回命中节点及与其相连的边 |

不带参数返回全量图谱(约 190 节点 / 340+ 边)。

**返回结构要点**:`nodes[]`(`{node_id, name, layer, sector, score, signals}`)、`edges[]`(`{src, dst, type, strength, channel, delay_ticks, sign}`)、`counts`。含 `disclaimer`。

---

#### `get_strategy_reports` — 策略沙盘推演报告

**用途**:按策略主题的沙盘推演报告与圆桌会议资料的 PDF 下载链接(10 分钟有效)。

**参数**:无。**返回**:`strategy_reports[]`(`{strategy, pdf_url, updated_at}`)、`round_table_documents[]`。含 `disclaimer`。

---

#### `get_info_feed` — 今日市场信息流

**用途**:多源聚合后**二次加工**的当日市场要闻:每条为「重要性打分(10 分制)+ 标题 + 摘要正文」。每日北京时间早间覆盖更新,**只反映当天**。**披露口径:5 分以上**(与 ADAMAS 产品端一致;`min_score` 传低于 5 的值会被钳回下限,返回中 `min_score_applied` 为实际生效值)。典型场景:晨会准备、盘前把当天要闻扫一遍,重点看高分。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `limit` | int | 否 | 30 | 返回条数,合法范围 1–200;越界为参数错误 |
| `min_score` | float | 否 | 5(披露下限) | 合法范围 0–10;可传更高只看高分(如 `8`),0–5 之间的合法值仍按披露下限 5 执行;越界为参数错误 |

**返回结构要点**:`items[]`(`{score, title, body}`,按文件序)、`count`。注意:条目**不含来源链接**(口径与 ADAMAS C 端一致);当日文件尚未生成时返回空列表并附说明。含 `disclaimer`。

---

#### `get_global_macro` — 全球宏观国别九维度报告

**用途**:先查有报告的经济体与九维度覆盖,再按经济体、维度和日期
读报告正文。只读、秒级返回;报告含模型生成的研究观点,
**引用时必须原文保留 `meta.disclaimer`**。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `country` | string | 否 | 不传返覆盖全景 | 经济体主键;必须取自无参返回的 `countries[].country_key` 或 `regions[].country_key` |
| `dimension` | string | 否 | 不传返该经济体的九维度覆盖 | 维度 key;必须与 `country` 一起传,取自 `dimensions[].key` 或 `cells[].key` |
| `report_date` | string | 否 | 最新一期 | 历史报告日期(`YYYY-MM-DD`);必须同时传 `country` + `dimension`,且应从最新正文返回的 `dates` 中选 |

**四种调用方式**:

| 调用 | 返回什么 |
|---|---|
| `get_global_macro()` | 覆盖全景:`countries[]`、`regions[]`、`dimensions[]`、`score_ready` |
| `get_global_macro(country="China")` | 中国的九个 `cells[]`,每格标出有无报告、最新日期和历史期数 |
| `get_global_macro(country="China", dimension="industry")` | 中国“主导产业”最新一期正文 + 全部可选历史日期 |
| 再加 `report_date="2026-08-04"` | 指定历史期正文;日期不在 `dates` 中时返回 error |

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
九个格子恒定返回,每格为 `{key, label, order, has_report, report_date,
periods}`。没有报告的格子也会保留,此时 `has_report=false`、`report_date=""`、
`periods=0`;这是正常空态,不是错误。

**报告正文返回要点**:`country_key`、`country_name`、`dimension`、`label`、
`report_date`、`content`(markdown 正文)、`dates[]`(该维度全部历史期,由新到旧)。
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
     "has_report": true, "report_date": "2026-08-04", "periods": 2},
    {"key": "trade", "label": "进出口", "order": 3,
     "has_report": false, "report_date": "", "periods": 0}
    // 此处仅节选 2 格；真实成功响应固定返回完整 9 格。
  ],
  "meta": {"note": "…", "disclaimer": "…须原文保留…"}
}
```

```jsonc
// 3) 调用:get_global_macro(
//      country="China", dimension="industry", report_date="2026-07-04")
{
  "country_key": "China",
  "country_name": "中国",
  "dimension": "industry",
  "label": "主导产业",
  "report_date": "2026-07-04",
  "content": "# 中国·主导产业\n\n…(markdown 正文)",
  "dates": ["2026-08-04", "2026-07-04"],
  "meta": {"note": "…", "disclaimer": "…须原文保留…"}
}
```

---

### 3.2 research 类(含模型观点,异步任务对)

research 类与 data 类的契约区别:**结果含模型生成的分析观点**;走独立的日额度(默认每 key 每日 20 次提交)与全局并发闸;均为异步——提交秒回 `task_id`,用 `get_research_task` 轮询;结果强制附 `disclaimer`,**引用必须原文保留**。

---

#### `submit_deep_research` — 提交深度研究问题

**用途**:基于 ADAMAS 研究知识库 + 联网检索的深度研究问答(含模型观点)。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `question` | string | 是 | — | 研究问题 |
| `mode` | string | 否 | `"auto"` | `flash`(快,约 1–2 分钟)/ `auto`(自动,约 2–5 分钟)/ `plus`(深,约 5–10 分钟)/ `pro`(最深,约 8–12 分钟) |

**返回结构要点**(提交成功):`task_id`、`status: "running"`、`eta_hint`(耗时预期)、`next_step`(轮询指引)。可能的错误:mode 非法;并发已满(`retry_after_seconds: 120`);服务维护窗口暂停接单(`retry_after_seconds: 300`);研究引擎暂不可用。

**示例**:

```jsonc
// 调用:submit_deep_research(question="存储芯片本轮涨价周期还能持续多久?驱动因素是什么?", mode="plus")
// 返回:
{
  "task_id": "6f9c1e2a-…",
  "status": "running",
  "eta_hint": "约 5-10 分钟",
  "next_step": "用 get_research_task(task_id='6f9c1e2a-…') 轮询结果,建议间隔 ≥30 秒"
}
```

---

#### `submit_stock_screen` — 提交产业链量化选股

**用途**:按中文产业链名称触发选股流程,综合已发布模型排名、相似度与产业链分析,
产出产业链图谱与候选标的(含模型观点)。约 3–8 分钟。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `industry_chain` | string | 是 | — | 产业链名称,1–200 字,如 `"存储芯片"`、`"光伏"` |

**返回结构要点**(提交成功):`task_id`、`status: "running"`、
`eta_hint: "约 3-8 分钟"`、`next_step`(建议轮询间隔 ≥60 秒)。选股全局同一时刻
只运行 1 个任务,并发已满时返回 error + `retry_after_seconds: 180`。

`done` 时 `result` 为选股引擎的完整结果对象,包含产业链图谱、候选公司与排名信息,
并带 `disclaimer`。本工具消耗 research 类 key 日额度及绑定账号的使用额度;
任务失败会自动退回本次账号用量,成功交付后不退。

**示例**:

```jsonc
// 调用:submit_stock_screen(industry_chain="存储芯片")
{
  "task_id": "a31b7c90-…",
  "status": "running",
  "eta_hint": "约 3-8 分钟",
  "next_step": "用 get_research_task(task_id='a31b7c90-…') 轮询结果,建议间隔 ≥60 秒"
}
```

---

#### `submit_notes_report` — 提交深度纪要报告

**用途**:深度纪要报告生成:多视角检索 + 深度推理 + 成稿(正文数千字,同时产出 PDF)。`topic` 既可以是研究主题(如「英伟达 GTC 大会要点」),也可以是一段会议/调研原始记录(≤2000 字)。

**参数**:`topic`(必填,1-2000 字)。

**返回结构要点**(提交成功):`task_id`、`status: "running"`、`eta_hint: "约 8-15 分钟"`、`next_step`(建议轮询间隔 ≥60 秒)。纪要生成全局同一时刻只跑 1 个,并发已满返回 error + `retry_after_seconds: 300`。

`done` 时的 `result`:`{title, markdown(纪要全文,直接给 AI 消费), pdf_download_url(PDF 成稿,3 天有效,给人阅读), pdf_download_expires_at, disclaimer}`。`markdown` 偶发拉取失败时为空串,此时用 `pdf_download_url`。

---

#### `get_research_task` — 轮询异步任务

**用途**:查询 `submit_deep_research` / `submit_stock_screen` / `submit_notes_report`
提交的任务状态与结果。**只能查询当前 API key 自己提交的任务**。此调用计入
data 类配额(rpm/日额度),**不消耗 research 日额度**——放心轮询,但请遵守建议间隔。

**参数**:

| 名称 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `task_id` | string | 是 | — | 提交时返回的任务 ID(UUID) |

**返回结构要点**(按状态):

| 状态 | 返回 |
|---|---|
| `running` | `{task_id, status: "running", progress: "<当前阶段描述>"}` |
| `done` | `{task_id, status: "done", result: {...}}` |
| `failed` | `{task_id, status: "failed", error: "<原因>"}` |

`done` 时的 `result` 结构:

- 深度研究:`{answer(完整回答 markdown), mode, engine, evidence_count, web_evidence_count, disclaimer}`。`mode` 回显你提交的档位;`engine` 为研究引擎标识(当前为 `"agentic"`);`evidence_count` / `web_evidence_count` 在当前引擎下不透出统计,恒为 0,请勿依赖,以 `answer` 正文中的引用为准;
- 产业链选股:选股引擎完整结果对象(产业链图谱、候选公司与排名信息)+ `disclaimer`;
- 深度纪要:`{title, markdown, pdf_download_url, pdf_download_expires_at, disclaimer}`(见 `submit_notes_report`)。

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

## 4. 异步任务模式(research 类完整生命周期)

```
submit_deep_research / submit_stock_screen / submit_notes_report
        │  秒级返回 task_id(此时任务已在服务端运行)
        ▼
get_research_task(task_id) ──► running(带 progress 阶段描述)──► 继续轮询
        │
        ├──► done   ──► result(含 disclaimer,引用原文保留)
        └──► failed ──► error(见下表,多数情况重新提交即可)
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

**实践建议**:

- 提交返回中的 `next_step` 字段已给出轮询指引,agent 直接照做即可;
- 等待期间不要空转:可先用 data 类工具取相关产业/标的的客观数据、起草报告框架(预置 prompts 即按此编排,见第 7 节);
- 任务有 **1 小时兜底 TTL**:若服务在任务运行中重启,遗留任务会在超时后被判为 `failed`(错误信息为「任务超时未完成(服务可能重启过),请重新提交」),重新提交即可;
- 轮询到 `done` / `failed` 后状态即为终态,结果已落库,可重复查询;
- `task_id` 与 API key 绑定,换 key 查不到。

## 5. 配额与限流

每个 API key 的默认配额(可按商务约定单独调整):

| 维度 | 默认值 | 超限表现 |
|---|---|---|
| 请求频率(rpm) | 60 次/分钟(令牌桶) | **HTTP 429** + `Retry-After` 头 + JSON `{error, retry_after_seconds}` |
| data 类日额度 | 2000 次/日 | `error: "数据类工具今日额度(2000)已用完"` + `retry_after_seconds`(到次日 0 点的秒数) |
| research 类日额度 | 20 次提交/日 | `error: "研究类工具今日额度(20)已用完"` + `retry_after_seconds`(到次日 0 点的秒数) |
| 深度研究全局并发 | 全部 key 合计 2 个在跑 | `error: "深度研究并发已满,请稍后重试"` + `retry_after_seconds: 120` |
| 产业链选股全局并发 | 全部 key 合计 1 个在跑 | `error: "选股任务并发已满,请稍后重试"` + `retry_after_seconds: 180` |
| 深度纪要全局并发 | 全部 key 合计 1 个在跑 | `error: "纪要生成并发已满,请稍后重试"` + `retry_after_seconds: 300` |
| research 类账号用量 | 按绑定账号的开通范围计 | `error: "今日使用已达上限，请联系工作人员"` |

### research 类工具与账号用量

research 三个提交工具(`submit_deep_research` / `submit_stock_screen` /
`submit_notes_report`)
除上表的 key 日额度外,**还消耗 API key 所绑定账号的使用额度**,与该账号在网页端
的用量算在一起。这三个工具每次调用都会真实运行对应的研究或选股流程,因此:

- **API key 必须绑定账号**才能调用 research 类工具。未绑定时返回
  `error: "该 API key 未绑定用户,无法使用研究类工具;请联系 ADAMAS 为 key 绑定账号"`
  ——data 类工具不受此限制,可照常使用;
- **`submit_deep_research` 选 `mode="pro"` 时用量按 2 倍计**(与网页端知识库的 Pro 单次问答模式一致，不是订阅档位),
  其余档位(`auto`/`flash`/`plus`)按 1 倍;
- **任务失败会自动退回本次用量**:上游报错、超时判死、你主动断开都会退,
  不必为失败的任务重复付出额度。**成功产出的任务不退**——包括你觉得结果不理想的情况;
- 账号额度用尽时返回 `error: "今日使用已达上限，请联系工作人员"`,
  与 key 日额度是两套独立限制,任一撞上都会被拒;
- 计费服务短暂不可用时 research 类工具会**拒绝提交**(返回
  `error: "计费服务暂时不可用,请稍后重试"` + `retry_after_seconds`),
  而不是免费放行——按 `retry_after_seconds` 退避即可。

说明:

- research 日额度只在**提交**时消耗;`get_research_task` 轮询走 data 类配额;
- research 全局并发闸是服务级保护(受上游算力约束),与你的用量无关也可能撞到——把「提交失败 + 按 `retry_after_seconds` 重试」做进你的任务队列逻辑;
- **频率(rpm)按每个 HTTP 请求计**,包含 `initialize`、`tools/list`、`prompts/*`、`ping` 等协议请求,不只是工具调用。超限返回 **HTTP 429**(带 `Retry-After` 头);
- **日额度按工具调用计**,超限以工具返回中的 `error` + `retry_after_seconds` 呈现(MCP 调用本身成功)。`retry_after_seconds` 给的是**到次日 0 点(北京时间)的秒数**——那才是额度真正重置的时刻,按它退避,不要每小时空试;
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

## 7. 预置 Prompts 与 WorkBuddy Skill

### 7.1 MCP Prompts(随 server 下发)

服务端预置 2 个 prompts,内置了「怎么用好这些工具」的调用顺序与引用规范。支持 MCP prompts 的客户端(如 Claude Code 中输入 `/` 可见,形如 `/mcp__adamas__industry_brief`)可直接选用:

| Prompt | 参数 | 产出 |
|---|---|---|
| `industry_brief`(行业跟踪简报) | `industry` 产业名 | 景气度 + 六维趋势 + 历史快照 + 全市场模型排名中的相关代表标的 → 成稿报告 PDF 与公司基本面跟踪要点,成文标 as_of、保留 disclaimer |
| `deep_research_report`(深度研究报告) | `topic` 研究主题 | 提交 plus 档深度研究 + 等待期间取产业数据与已发布模型排名 → 综合成文(研究结论注明来自 ADAMAS 研究引擎 + 数据佐证标 as_of + 交叉验证) |

不支持 prompts 的客户端,可把上述编排写进你自己的系统提示词,方法论同源于第 7.2 节的 Skill。

### 7.2 WorkBuddy / OpenClaw Skill 包

Skill 包与本文档一起发布在**公开接入仓库** <https://github.com/felixhjh-2/adamas-mcp-connect>
(路径 `plugins/adamas-research-report/skills/adamas-research-report/`),内容为「ADAMAS 投研报告」方法论:先看地图再取数、代码先解析、全球宏观先拉覆盖全景再读正文、数据与观点分开取分开写、限流退避、成文规范(日期标注、三类内容区分、disclaimer 原文保留、六维趋势符号含义)以及六个常用剧本(行业跟踪简报/个股解读/全球宏观对比/产业链量化选股/深度专题报告/晨会纪要一页)。

安装方式:

- **WorkBuddy**:先接入 ADAMAS MCP 连接器(见 2.1),再下载上述仓库,把 Skill 目录作为技能导入(入口一般在 技能/Skill 管理 → 导入本地技能包);
- **Claude Code**:插件一步装齐(MCP 连接 + Skill,key 走环境变量 `ADAMAS_API_KEY`):
  会话内 `/plugin marketplace add felixhjh-2/adamas-mcp-connect` → `/plugin install adamas-research-report@adamas`;
- **OpenClaw / 其他支持 Agent Skills 的框架**:把 Skill 目录放入框架的 skills 目录即可(触发条件与用法在 `SKILL.md` frontmatter 中)。

Skill 与 MCP prompts 方法论同源:装了 Skill 的 agent 会主动按 ADAMAS 推荐的顺序调用工具并遵守成文规范,显著降低集成后的提示词调试成本。

## 8. FAQ / 故障排查

**Q:HTTP 401,提示「缺少 API key」或「API key 无效或已禁用」?**
检查 `Authorization` 头是否为 `Bearer <your-api-key>` 格式(注意 `Bearer` 后有空格)、key 是否复制完整(以 `adamas_` 开头)。仍失败则 key 可能已被禁用或未开通,联系 ADAMAS 确认。

**Q:HTTP 401,提示「API key 已过期」?**
你的 key 设有有效期且已到期。联系 ADAMAS 续期即可,续期立即生效,无需换 key。

**Q:HTTP 421(Misdirected Request)?**
服务端开启了 DNS-rebinding 保护,只接受 Host 白名单内的请求(`www.adamas-research.com` 等)。直连官方端点不会遇到此问题;若你在自建网关/反向代理后面转发请求,必须**透传原始 Host 头**(如 nginx `proxy_set_header Host www.adamas-research.com;`),或联系 ADAMAS 把你的域名加入白名单。

**Q:返回里带 `error` 和 `retry_after_seconds`(额度/并发超限)?**
这是结构化的业务失败信号:`CallToolResult.isError=true`,内容中保留 `error` 和退避时间;它不是 HTTP/传输故障。按 `retry_after_seconds` 的秒数等待后重试;把它做进你的重试逻辑,不要密集重试。日额度类的 `retry_after_seconds` 指向**次日 0 点(北京时间)**的剩余秒数,当日不必再试。

**Q:收到 HTTP 429?**
频率超限(每分钟调用数)走 HTTP 429,响应带标准 `Retry-After` 头和 `retry_after_seconds` 字段,按其中任一等待后重试即可。注意频率是按**每个 HTTP 请求**计的,连接握手、列工具等协议请求也计入。

**Q:任务 `failed`,错误是「任务超时未完成(服务可能重启过),请重新提交」?**
服务滚动更新/重启会中断在跑任务,遗留任务超过 1 小时 TTL 后自动判 failed。重新提交同样的问题即可,重新提交会正常消耗一次 research 额度。

**Q:调用工具时返回「服务即将更新维护,暂停接收新任务,请几分钟后重试」?**
服务处于更新窗口(排空中),会暂停所有新工具调用,已接纳的调用会继续跑完。
按返回的 `retry_after_seconds`(300 秒)稍后重试即可。

**Q:研究结果里 `evidence_count` 是 0?**
正常。evidence 计数在当前引擎(`engine: "agentic"`)下不透出统计,以 `answer` 正文中的引用为准;`mode` 回显你提交的档位。

**Q:轮询 `get_research_task` 返回「引擎状态暂不可查,请稍后再试」?**
研究引擎瞬时不可达,任务本身仍在跑,状态显示为 running。按正常间隔继续轮询即可;若持续超过任务耗时预期上限,参考 TTL 条目处理。

**Q:`get_company_tracking` 返回了目录但 `content` 为空、带 `content_error`?**
报告全文存储瞬时不可用,目录不受影响。稍后重试;持续失败请联系 ADAMAS。

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
