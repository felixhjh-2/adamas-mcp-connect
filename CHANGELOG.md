# CHANGELOG

## 2026-09-04

- OAuth 动态客户端注册新增 ChatGPT、Cursor Web、VS Code 与 IPv6 loopback 回调支持，
  保留 Claude 与 IPv4/localhost；网页路径可动态生成，但主机必须精确命中且使用 HTTPS；
- 授权服务器发现文档显式声明 public client `token_endpoint_auth_method=none`，
  public client 只走 S256 PKCE、不要求 `client_secret`；confidential client 的 secret
  继续只存 SHA-256，并在 token/revoke 时校验；
- README 与完整接入文档补齐 ChatGPT OAuth 步骤、默认回调主机和排障说明。

## 2026-08-26

- `get_global_macro` 改为每个经济体×维度只提供最新报告;
  停止按日期选择旧版，移除期数与日期目录。为避免旧客户端在滚动升级时
  schema 失配，日期参数仅暂作当前版校验兼容，新接入必须省略。
- 公司跟踪的历史报告契约保持不变。
- Claude Code 插件版本升级到 2.3.1，确保客户端刷新 latest-only Skill。

## 2026-08-25

Standard 公开契约同步为 15 个工具:

- 新增只读 `get_global_macro`,可先拉取经济体与九维度覆盖全景,
  再读某个经济体的报告正文;
- 公开文档与 Skill 补齐了宏观使用顺序、九维度口径及
  `score_ready=false` 时不得臆造分数的约束;
- 合规口径明确 `China-Taiwan` 只在 `regions` 中出现,不计入国家数;
- 新增 Kimi Code 接入说明:通过 `~/.kimi-code/mcp.json` 配置 remote HTTP MCP,
  Bearer key 从 `ADAMAS_API_KEY` 环境变量读取,并补齐 Agent Skill 安装路径;
- Claude Code 插件版本升级到 2.3.0。

## 2026-08-24

Standard 公开契约同步为 14 个工具:

- 明确 `get_model_picks`(已发布模型选股排名)与 `submit_stock_screen`
  (产业链量化选股任务)属于 Standard,并补齐 `check_company_coverage` 的入口说明;
- Skill 改为公司名单先批量查覆盖,并禁止把 ADAMAS 细分产业名直接当成
  `get_model_picks.asset_class_l1`;
- 能力地图口径补充 `model_picks_as_of`,客户端接入说明与业务错误的
  `CallToolResult.isError` 语义同步线上契约;
- Claude Code 插件版本升级到 2.2.0。

## 2026-08-11

文档补漏与错误文案对齐:

- **补上 `check_company_coverage` 的完整说明**(此前文档第 3 节整个漏了这个工具)。
  拿到一批公司(股票池/名单)时用它一次问清哪些有跟踪报告,**不要对
  `get_company_tracking` 循环单查** —— 几十个往返又慢又会撞 60 次/分钟的频率限制,
  还会把每家的报告全文都拉回来。概述里的工具数同步更正为 14 个(10 data + 4 research);
- **research 并发已满的错误文案按闸区分**,与本文档逐字一致:
  「深度研究并发已满,请稍后重试」/「选股任务并发已满,请稍后重试」/
  「纪要生成并发已满,请稍后重试」(此前服务端统一回一句笼统文案,照文档做
  错误分流会匹配不上)。三个闸各自独立,退避秒数仍为 120 / 180 / 300;
- `get_company_tracking` 没找到公司时新增 `did_you_mean`(相近公司名);
- `list_capabilities` 的字段表与示例补上 `industry_catalog`。

产业类工具更好用了 —— 起因是发现 agent 常按申万/中信的一级行业名去查产业
(「新能源」「医药生物」),而 ADAMAS 用的是自建的细分产业名(「光伏」「固态电池」
「CXO」),对不上就查不到。

- `list_capabilities` 新增 **`industry_catalog`**:一次返回**全部产业名**(约190个,
  仅约 2KB)。这是 `get_industry_scores` / `get_industry_graph` / `get_industry_report`
  三个工具**唯一有效的取值集合**,查产业前照它对齐名称即可;
- 产业/图谱/公司类工具**没查到时会把可选值一并返回**:
  `available_industries`(全部产业名)、`available_nodes_by_sector`(按 sector 分组的
  图谱节点)、`did_you_mean`(相近公司名)。照着改一次就能命中,不必反复试;
- `get_industry_scores` 新增 **`include_summary`**(默认 `true`,返回结构不变)。
  传 `false` 省略各产业的 `tracking_summary` 全文,全量返回体量降到约 1/5 ——
  「先按分数/趋势筛出几个产业,再单查它们的摘要」这种用法建议改用它,
  可以少占大量上下文。全量返回的 `meta.size_warning` 会给出本次的实际体量。

详见 [docs/USAGE.md](docs/USAGE.md) 中 `get_industry_scores` 一节。

## 2026-07-31

research 类工具(`submit_deep_research` / `submit_notes_report` / `submit_stock_screen`)
开始**按 API key 所绑账号的额度计量**,与网页端同一套账:

- API key **必须绑定账号**才能调用 research 类;data 类不受影响,照常使用;
- `submit_deep_research` 选 `mode="pro"` 用量按 2 倍计,其余档位 1 倍;
- **任务失败自动退回**(上游报错、超时判死、主动断开都退);成功产出的不退;
- 计费链路暂时不可用时 research 类**拒绝提交**并给 `retry_after_seconds`,
  不会静默放行 —— 按该值退避即可。

详见 [docs/USAGE.md](docs/USAGE.md) 第 5 节「research 类工具与账号用量」。

## v2 — 2026-07-25

新增:深度纪要报告生成(`submit_notes_report`,markdown 全文+PDF)、每日信息流
(`get_info_feed`)、产业关联图谱(`get_industry_graph`,189 节点/343 传导边)、
产业报告 PDF(`get_industry_report`)、策略沙盘报告(`get_strategy_reports`)、
公司跟踪历史期全文(`get_company_tracking` 增 `report_date`)。

改进:所有工具返回 structured output;深度研究结果 `mode` 回显提交档位
(引擎标识移至 `engine`);key 支持有效期(到期 401,续期立即恢复)。

## v1 — 2026-07-24(10 工具)

首发:资产搜索/模型选股/产业景气度/公司跟踪 +
深度研究/产业链选股(异步任务)+ 能力地图。3 个预置 prompts 与 WorkBuddy Skill 包。
