# CHANGELOG

## 2026-10-16 · 2.6.3 接入材料

- 原生知识库部分交付结果可保留本轮已收到的可选来源映射与证据统计；旧结果或来源不足时仍可能缺失，不能据此宣称出处已核验。
- 保留停止、部分交付与计费边界；来源映射不表示回答完整、已停止或已退款，W 标记仍不承诺原始网页定位。
- Standard 保持28个工具与2个 prompts，工具参数与服务契约版本不变。

## 2026-10-16 · 2.6.2 接入材料

- 原生知识库完成结果的可选 `query` 返回保存的原问题，重新生成沿用该轮问题；旧后端字段可能为空。
- 说明可选 `meta.citable_count` / `meta.dropped_uncitable_count`，区分实际可引用证据与缺少安全来源的检索项；统计不能代替事实核验。
- Standard 仍为28个工具与2个 prompts；新增元数据为可选字段，实际支持范围以端点发现与返回为准。

## 2026-10-15 · 2.6.1 接入材料

- 补充研究正文 E/W 标记的使用说明：E 可对照安全文档标识与来源日期；W 仅指本轮联网补充条目，不承诺原始网页定位或已核实 URL。
- 明确来源映射与 evidence 计数不能替代逐条出处核验；来源不足如实说明，不补造编号、标题或链接，引用保留原文免责声明。
- Standard 保持28个工具与2个 prompts；材料版本与服务契约分别说明，实际能力以当前端点发现为准。

## 2026-10-14 · 2.6.0 接入材料

- Standard 增为28个工具：原生知识库新建/续问与最新回答重新生成，6个 research 提交入口与22个 data 入口；实际能力以当前端点发现为准。
- 说明原 task_id 与原生会话/消息/生成轮次、网页连续历史、原回答快照显式只读查询和恢复范围、最近5版显示与完整快照的区别。
- 原回答大快照按UTF-8字节偏移/base64分片只读获取，整体验证长度及SHA后再解码，保持每页权限核验；小快照仍直接返回对象。
- 停止请求按本轮 generation_id，不能停止后续轮次；停止不等于终态或退款，部分新交付仍计入用量。
- 提醒客户端刷新或重连工具列表；材料版本2.6.0与服务契约2026-10-14.2分别说明。

## 2026-10-14 · 2.5.0 接入材料

- Standard 扩充为26个工具：增加网页知识库会话/消息读取与管理、显式公开分享/撤销、网页生成停止请求、热点纪要历史，以及指定公司/报告期数的横向研究。
- 明确网页会话和研究任务分离；异步研究不自动创建网页会话，也不提供取消入口。网页停止状态含 not_cancellable_here，不能据此宣称已停止或退款。
- 分享须明确公开意图，删除会话不撤销独立分享快照；有状态操作超时先核对原资源，避免重复分享或提交。
- 接入材料版本为2.5.0；新增能力须待服务端启用，当前授权与参数始终以端点发现结果为准。

## 2026-10-13 · 研究归属保护说明

- 明确持久付费任务按原 key 与绑定账号归属，改绑不转让历史；更换账号须重新签发 key。
- 历史游标绑定账号，旧游标失效时重取首页；新命名会话启用账号隔离，已受理任务保留原请求恢复。

## 2026-10-13 · 接入示例修正

- 快速开始示例兼容合法的空摘要日期，显示“日期未提供”并继续后续查询；离线验证覆盖整个示例调用流程。
- 纠正研究 evidence 计数恒为 0 的说明：计数透传上游统计，且不等于可追溯引用数量；来源仍以安全映射及引用说明为准。

## 2026-10-13 · 2.4.0 正式发布

- 插件正式版本升级到 2.4.0；Standard 提供 17 个工具与 2 个 prompts，实际授权范围以当前端点发现结果为准；
- 新增 key 额度自查与任务历史；历史支持状态/类型过滤及绑定当前 key 与筛选条件的 cursor 分页；
- 三个付费提交工具支持可选 `idem_key` 与持久回执，同键同完整参数恢复原任务；省略键返回生成的 `auto:<UUIDhex>` 恢复键。受理未知保留原任务，先历史定位再轮询，不换键重投，也不把等待或断开当作已退款；
- 补齐结构化 `error_class` / `recovery`、公司正文与 PDF 链接交付状态、图谱一跳邻居及 sector 边界、信息流文件日期与 stale；
- 深度研究返回可用的安全文档映射与引用说明；映射可能为空，不承诺完整来源映射，引用保留免责声明。

## 2026-10-12 · 候选，尚未发布

- Standard 候选契约同步为 17 个工具：新增额度自查 `get_my_quota` 与任务历史 `list_my_research_tasks`，历史支持状态/类型过滤及游标分页；
- 授权目录与工作流发现、结构化 `error_class` / `recovery`、提交回执恢复同步至 README、使用文档、Skill 和示例，不盲目重复付费提交；
- 三个付费提交工具候选增加可选 `idem_key` 与持久提交回执：同键同完整业务参数返回原任务、不重复扣本次账号用量；空键每次仍新建意图，但回执与轮询返回生成的 `auto:<UUIDhex>` 恢复键；先历史定位、再轮询取键，需要恢复时显式传返回键与完整原参数，轮询不会自动重新派发，新键不能恢复旧任务；
- 纠正旧条目的断开/退款说法：客户端断开不代表任务取消或退款，以恢复后的服务端终态及结算结果为准；
- 公司覆盖统一歧义确认，正文交付区分完整/截断/不可用；图谱补齐一跳邻居并遵守 sector 边界；信息流披露文件修改日期与 stale；
- 研究结果增加可用的安全文档映射与引用说明，映射可能为空，不保证所有回答可审计，也不编造标题/链接；
- 插件候选版本升级到 2.4.0-rc.1；实际能力以当前端点发现结果为准，本记录不表示生产上线。

## 2026-09-16

- 订正 `check_company_coverage` 返回结构说明与示例：明确 `covered[].asked_as` 数组口径、`not_covered[]` 结构体数组与 `ignored`、`summary.unique_companies` 字段；
- 订正 `get_company_tracking` 与 `check_company_coverage` 参数支持：补充股票代码（如 `300750.SZ`）与交易所类别后缀（如 `万科A`、`美团-W`）自动归一化及模糊多匹配候选返回说明；
- 清理 `get_strategy_reports` 中已下线的旧版 `round_table_documents` 字段及旧称残留；
- 补齐配额表中单 key 研究任务并发限制（每个 key 同一时刻只允许 1 个研究任务进行中，超限退避 60 秒）；
- 优化 Python SDK 快速开始代码中 `streamable_http_client` 导入容错；
- 明确 `get_industry_graph` 中 `signals` 六维具名趋势对象结构。

## 2026-09-05

- Claude Code 接入改为 OAuth 优先：补齐无请求头的 `claude mcp add`、
  `claude mcp login` / `/mcp` 授权步骤，并明确现有插件连接仍采用
  `ADAMAS_API_KEY` Bearer key；
- ChatGPT 接入补齐 Plugins / Apps 界面差异、账号与工作区前提，以及
  Business、Enterprise、Edu、Pro 当前支持范围；
- README、完整使用文档与 FAQ 统一说明 public client、S256 PKCE、refresh token、
  动态回调主机和 OAuth / Bearer 的适用边界。

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
