---
name: adamas-research-report
description: 用 ADAMAS 投研数据写专业研究报告/晨会纪要/行业跟踪/全球宏观对比。当用户要写行业分析、个股解读、宏观分析或投研报告,且已接入 ADAMAS MCP 连接器时使用。
---

# ADAMAS 投研报告技能

前提:已在连接器中接入 ADAMAS MCP(工具名以 `list_capabilities`、`get_industry_scores` 等出现)。

## 核心方法论

1. **先看地图再取数**:任何任务先调 `list_capabilities`,确认覆盖范围和各数据域的
   `freshness`(数据截止日,包括模型选股的 `model_picks_as_of`)。行情为交易日
   盘后导入,别把旧数据当今天的。
2. **代码先解析**:用户说的公司名先 `search_assets` 转成 `asset_code`,再调其他工具。
2.5 **产业名先对齐,别按行业分类猜**:产业类工具(`get_industry_scores` /
   `get_industry_graph` / `get_industry_report`)只认 ADAMAS 自建的细分产业名,
   取值集合就是 `list_capabilities` 返回的 `industry_catalog`(约190个)。
   **没有**「新能源」「医药生物」「电力设备」这类申万/中信一级行业 —— 它们要拆成
   「光伏」「风电」「储能」「锂电池」「固态电池」这样的细分名分别查。
   万一没命中,error 里的 `available_industries` 会给全名单,照着改一次就行。
2.6 **全球宏观先拉全景,再读正文**:先无参调 `get_global_macro()`,
   从 `countries` / `regions` 取官方 `country_key`,再传 `country`。某经济体
   的九维度覆盖用 `get_global_macro(country=X)`,报告正文用
   `get_global_macro(country=X, dimension=Y)`;要做跨期对比,先从最新正文返回的
   `dates` 选日期,再加 `report_date`。`China-Taiwan` 只是 `regions` 中的
   中国台湾地区,不得写成国家或计入国家数。当 `score_ready=false` 时,
   不得臆造、推断、排名或用颜色代替尚未上线的宏观分数。
3. **数据与观点分开取、分开写**:
   - 客观数据、已发布量化结果与成稿报告:`get_model_picks`(最新模型选股排名)、
     `get_industry_scores`(景气度)、
     `check_company_coverage`(批量查哪些公司有跟踪报告)、
     `get_company_tracking`(公司跟踪全文,可传 report_date 取历史期做跨期对比)、
     `get_industry_graph`(产业链传导图谱)、`get_info_feed`(当日要闻打分摘要)、
     `get_global_macro`(全球宏观九维度报告,可传 report_date 取历史期)、
     `get_industry_report`/`get_strategy_reports`(成稿 PDF 链接,直接交付给读者);
   - **拿到一批公司(股票池/名单)时,先 `check_company_coverage` 一次问清覆盖情况,
     再对命中的用 `get_company_tracking` 取全文** —— 不要对后者循环单查:
     几十个往返又慢又会撞 60 次/分钟的频率闸,还会把每家的全文都拉回来。
   - 模型观点:`submit_deep_research`(深度研究,异步)、
     `submit_stock_screen`(产业链量化选股,异步)、
     `submit_notes_report`(深度纪要成稿,异步)。
     提交后按返回的 `next_step` 轮询 `get_research_task`,等待期间先取客观数据并起草框架;
     ⚠️ 这三个会**消耗所属账号的使用额度**(客观数据类不消耗):
     · 同一个问题不要反复提交 —— 失败会自动退回,但成功产出的不退,即使你对结果不满意;
     · `submit_deep_research` 选 `mode="pro"` 用量按 2 倍计,按需要选档而不是默认拉满;
     · 若返回"该 API key 未绑定用户",说明这把 key 还没绑账号,联系 ADAMAS 处理,重试无用。
4. **遇到限流**:返回带 `retry_after_seconds` 时按值等待,不要密集重试。

## 成文规范(必须遵守)

- 每个引用的数字标注数据日期,格式如「(ADAMAS 数据,截至 2026-07-07)」;
- 区分三种内容并让读者能分辨:①ADAMAS 客观数据 ②ADAMAS 模型观点(深度研究/选股/景气度打分)
  ③你自己的推断与综合;
- 报告结尾**原文保留**工具返回中的 disclaimer(免责声明),一字不改;
- 六维趋势符号含义:↗ 改善 / → 持平 / ↘ 恶化(维度:当前/预期/供给/成本/竞争/出口)。

## 常用剧本

**行业跟踪简报**:`get_industry_scores(industry=X, include_history=true)` →
`get_model_picks(top_n=30)` 取已发布排名,再按业务相关性筛代表标的 →
可选 `get_industry_report` 取成稿 PDF → 对公司名单先用 `check_company_coverage`
批量确认覆盖,再对命中者取 `get_company_tracking` →
成文:景气度结论+趋势拆解(六维符号)+模型偏好+历史快照+代表公司基本面跟踪。

> `get_model_picks.asset_class_l1` 只接受资产表 L1 分类(如「有色金属」),
> 与 `industry_catalog` 的 ADAMAS 细分产业名不是同一套口径。只有已通过
> `search_assets` 确认精确 L1 时才传该参数;不要把「光伏」「存储芯片」等细分产业名
> 直接当作 `asset_class_l1`。

**个股解读**:`search_assets`(解析 asset_code)→ `get_company_tracking(公司名)`
→ 需要跨期对比时传 `report_date` 取历史期 → 可选用
`get_model_picks(top_n=100)` 确认该标的是否进入本期前 100(未出现只表示不在返回区间)
→ 成文:基本面跟踪要点+跨期变化+已发布模型排名参考。

**全球宏观对比**:`get_global_macro()` 拿覆盖全景、九维度字典与
`score_ready` → 对目标经济体分别调 `get_global_macro(country=X)` 确认哪些维度
有报告 → 只对 `has_report=true` 的格子调
`get_global_macro(country=X, dimension=Y)` 取最新正文 → 需要跨期时从 `dates`
选取历史日期加 `report_date` 重查 → 成文:按同一维度比较,每段标明
`report_date`,原文保留 `disclaimer`;若 `score_ready=false`,只写报告内容,
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
`get_industry_scores(industry=X)` 单查拿摘要,再用 `get_info_feed` 补当日要闻
→ `get_model_picks(top_n=10)` 补最新模型偏好 →
一页式:今日景气度看点+产业变化+模型偏好+市场要闻+风险提示+免责。

> 不要用不带参数的 `get_industry_scores()` 做这一步:它会把全部约 190 篇跟踪摘要
> 全文一次灌进上下文(比上面那种大 5 倍),而你只需要其中 3-5 篇。
