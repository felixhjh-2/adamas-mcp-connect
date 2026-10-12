---
name: adamas-research-report
description: 用 ADAMAS 投研数据写专业研究报告/晨会纪要/行业跟踪/全球宏观对比。当用户要写行业分析、个股解读、宏观分析或投研报告,且已接入 ADAMAS MCP 连接器时使用。
---

# ADAMAS 投研报告技能

前提:已在连接器中接入 ADAMAS MCP(工具名以 `list_capabilities`、`get_industry_scores` 等出现)。

候选版本(2026-10-12，尚未发布)：本技能只使用标准档 17 个工具。先发现当前端点能力；旧端点不具备的候选工具不要假定可用。

## 核心方法论

1. **先看地图再取数**:任何任务先调 `list_capabilities`,确认覆盖范围和各数据域的
   `service`(授权工具/工作流，精确参数以 `tools/list` 为准)与
   `freshness`(数据截止日,包括模型选股的 `model_picks_as_of`)。行情为交易日
   盘后导入,别把旧数据当今天的。
2. **代码先解析**:用户说的公司名先 `search_assets` 转成 `asset_code`,再调其他工具。
2.5 **产业名先对齐,别按行业分类猜**:产业类工具(`get_industry_scores` /
   `get_industry_graph` / `get_industry_report`)只认 ADAMAS 自建的细分产业名,
   取值集合就是 `list_capabilities` 返回的 `industry_catalog`(约190个)。
   **没有**「新能源」「医药生物」「电力设备」这类申万/中信一级行业 —— 它们要拆成
   「光伏」「风电」「储能」「锂电池」「固态电池」这样的细分名分别查。
   未命中看 `did_you_mean`(最多 5 个候选)，完整名称从 `industry_catalog` 获取，不依赖 `available_industries`。
2.6 **全球宏观先拉全景,再读正文**:先无参调 `get_global_macro()`,
   从 `countries` / `regions` 取官方 `country_key`,再传 `country`。某经济体
   的九维度覆盖用 `get_global_macro(country=X)`,报告正文用
   `get_global_macro(country=X, dimension=Y)`。每个经济体×维度只提供最新报告,
   不要请求旧版本或生成跨期目录。`China-Taiwan` 只是 `regions` 中的
   中国台湾地区,不得写成国家或计入国家数。当 `score_ready=false` 时,
   不得臆造、推断、排名或用颜色代替尚未上线的宏观分数。
3. **数据与观点分开取、分开写**:
   - 客观数据、已发布量化结果与成稿报告:`get_model_picks`(最新已发布的量化选股
     Top N，排名对象是股票/资产，不是不同模型)、
     `get_industry_scores`(景气度)、
     `check_company_coverage`(批量查哪些公司有跟踪报告)、
     `get_company_tracking`(公司跟踪全文,可传 report_date 取历史期做跨期对比)、
     `get_industry_graph`(焦点及一跳邻居的产业链图谱，sector 同时限制两者)、`get_info_feed`(最新文件的要闻摘要)、
     `get_global_macro`(全球宏观九维度最新报告)、
     `get_industry_report`/`get_strategy_reports`(成稿 PDF 链接,直接交付给读者);
   - **拿到一批公司(股票池/名单)时,先 `check_company_coverage` 一次问清覆盖情况,
     先确认 `ambiguous` 的准确公司名，再对 covered 命中的用 `get_company_tracking` 取全文** —— 不要对后者循环单查:
     几十个往返又慢又会撞 60 次/分钟的频率闸,还会把每家的全文都拉回来。
   - 模型观点:`submit_deep_research`(深度研究,异步)、
     `submit_stock_screen`(产业链量化选股,异步)、
     `submit_notes_report`(深度纪要成稿,异步)。
     提交后按返回的 `next_step` 轮询 `get_research_task`,等待期间先取客观数据并起草框架;
     ⚠️ 这三个会**消耗所属账号的使用额度**(客观数据类不消耗):
     · 同一个业务不要反复提交；确认失败后按服务端结算结果处理，状态未知不代表失败或已退款，成功产出的不退;
     · `submit_deep_research` 选 `mode="pro"` 用量按 2 倍计,按需要选档而不是默认拉满;
     · 若返回"该 API key 未绑定用户",说明这把 key 还没绑账号,联系 ADAMAS 处理,重试无用。
4. **额度与恢复先自查**:批量调用或提交前用 `get_my_quota`(免日扣减，仍计 RPM)；提交回执丢失先用 `list_my_research_tasks` 恢复 task_id，再轮询，不能直接重复付费提交。历史支持 limit/status/kind/cursor，翻页保留原筛选；只读落库摘要，不代表上游最新状态。
   三个付费提交工具候选支持可选 `idem_key`：非空须 ≤128 个 ASCII 字符，匹配 `[A-Za-z0-9][A-Za-z0-9_.:-]*`。同一 API key、同一工具内，同键与完整业务参数一致时返回原任务、不重复扣本次账号用量；深研 `session_id` 也纳入业务参数。换参冲突为 `BadParam`，新业务用新键；新键不等于恢复原任务。无键兼容每次 RPC 新建意图，但回执与本候选创建任务的轮询会返回生成的 `auto:<UUIDhex>` 恢复键。丢回执先历史找 task_id，再轮询取键；需要恢复提交时，向同一工具显式传返回键与完整原参数。继续传空键仍是新意图，轮询不会自动重新派发付费任务。`idempotency_persisted:true` 表示提交意图已记录，受理可能待确认；先查历史/轮询，不盲重投，不推断已退款。按可选 `task_status` 与 `progress` 查看原任务提示，当前结果仍用轮询获取。
5. **错误按恢复指引处理**:检查 `isError`、`error_class` 与 `recovery.action`，仅 `retry_safe=true` 才自动重放；按可选 `retry_after_seconds` 等待，不盲重试。

## 成文规范(必须遵守)

- 每个引用的数字标注数据日期,格式如「(ADAMAS 数据,截至 2026-07-07)」;
- 区分三种内容并让读者能分辨:①ADAMAS 客观数据 ②ADAMAS 模型观点(深度研究/选股/景气度打分)
  ③你自己的推断与综合;
- 报告结尾**原文保留**工具返回中的 disclaimer(免责声明),一字不改;
- 六维趋势符号含义:↗ 改善 / → 持平 / ↘ 恶化(维度:当前/预期/供给/成本/竞争/出口)。

- 公司正文先检查 `meta.content_status`：`complete` 才是本次完整交付，`truncated` 仅为部分正文，`omitted` / `unavailable` 不代表读过全文。全文错误保留目录，不能据目录编造正文。
- 信息流先检查 `availability` / `stale`；`as_of` 与 `source_updated_at` 来自文件 mtime，不是逐条事件日期。旧文件标明旧日期，not_generated 的空列表不代表市场没有新闻。
- 深度研究的 `doc_id_mapping` 常为空；有映射时按 `citation_note` 使用，无映射保留原 E 编号并说明引用信息有限，不编造文档标题/链接，也不宣称全部回答可审计。

## 常用剧本

**行业跟踪简报**:`get_industry_scores(industry=X, include_history=true)` →
`get_model_picks(top_n=30)` 取最新已发布的量化选股 Top N,再按业务相关性筛代表标的 →
可选 `get_industry_report` 取成稿 PDF → 对公司名单先用 `check_company_coverage`
批量确认覆盖,再对命中者取 `get_company_tracking` →
成文:景气度结论+趋势拆解(六维符号)+量化选股结果+历史快照+代表公司基本面跟踪。

> `get_model_picks.asset_class_l1` 只接受资产表 L1 分类(如「有色金属」),
> 与 `industry_catalog` 的 ADAMAS 细分产业名不是同一套口径。只有已通过
> `search_assets` 确认精确 L1 时才传该参数;不要把「光伏」「存储芯片」等细分产业名
> 直接当作 `asset_class_l1`。

**个股解读**:`search_assets`(解析 asset_code)→ `get_company_tracking(公司名)`
→ 需要跨期对比时传 `report_date` 取历史期 → 可选用
`get_model_picks(top_n=100)` 确认该标的是否进入本期前 100(未出现只表示不在返回区间)
→ 成文:基本面跟踪要点+跨期变化+最新量化选股结果参考。

**全球宏观对比**:`get_global_macro()` 拿覆盖全景、九维度字典与
`score_ready` → 对目标经济体分别调 `get_global_macro(country=X)` 确认哪些维度
有报告 → 只对 `has_report=true` 的格子调
`get_global_macro(country=X, dimension=Y)` 取最新正文 → 成文:按同一维度比较各经济体的
最新报告,每段标明返回的最新 `report_date`,原文保留 `disclaimer`;
全球宏观不做历史版本对比,公司跟踪仍可用 `history` / `report_date` 跨期对比;
若 `score_ready=false`,只写报告内容,
不生成任何“周期分数”或经济体排名。

**产业链量化选股**:`submit_stock_screen(industry_chain=X)` → 按返回的
`next_step` 用 `get_research_task` 轮询(建议间隔≥60秒) → 完成后对结果公司名单先调
`check_company_coverage` 批量查覆盖,再取命中者的 `get_company_tracking` 做基本面交叉验证 →
成文:产业链逻辑+标的建议+基本面佐证+风险提示。

**深度专题报告**:`submit_deep_research(question, mode="plus")` → 等待期间用
data 工具取相关行业/标的客观数据 → 轮询拿到研究结论 → 综合成文(研究观点注明
来自 ADAMAS 研究引擎,数据佐证标 as_of,交叉验证部分是你自己的)。

**晨会纪要一页**:`get_industry_scores(include_summary=false)`(全量打分+六维趋势,
**不带摘要全文**)→ 挑出分数最高/变动明显的 3-5 个 → 对这几个
`get_industry_scores(industry=X)` 单查拿摘要,再用 `get_info_feed` 核对新鲜度后补最新要闻
→ `get_model_picks(top_n=10)` 补最新已发布的量化选股 Top 10 →
一页式:今日景气度看点+产业变化+量化选股结果+市场要闻+风险提示+免责。

> 不要用不带参数的 `get_industry_scores()` 做这一步:它会把全部约 190 篇跟踪摘要
> 全文一次灌进上下文(比上面那种大 5 倍),而你只需要其中 3-5 篇。
