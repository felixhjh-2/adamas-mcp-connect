---
name: adamas-research-report
description: 用 ADAMAS 投研数据写专业研究报告/晨会纪要/行业跟踪。当用户要写行业分析、个股解读、投研报告,且已接入 ADAMAS MCP 连接器时使用。
---

# ADAMAS 投研报告技能

前提:已在连接器中接入 ADAMAS MCP(工具名以 `list_capabilities`、`get_industry_scores` 等出现)。

## 核心方法论

1. **先看地图再取数**:任何任务先调 `list_capabilities`,确认覆盖范围和各数据域的
   `freshness`(数据截止日)。行情为交易日盘后导入,别把旧数据当今天的。
2. **代码先解析**:用户说的公司名先 `search_assets` 转成 `asset_code`,再调其他工具。
3. **数据与观点分开取、分开写**:
   - 客观数据:`get_model_picks`(模型选股)、`get_industry_scores`(景气度)、
     `get_company_tracking`(公司跟踪全文,可传 report_date 取历史期做跨期对比)、
     `get_industry_graph`(产业链传导图谱)、`get_info_feed`(当日要闻打分摘要)、
     `get_industry_report`/`get_strategy_reports`(成稿 PDF 链接,直接交付给读者);
   - 模型观点:`submit_deep_research`(深度研究,异步)、`submit_stock_screen`(产业链选股,异步)、
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
`get_model_picks(asset_class_l1=对应行业)` → 可选 `get_industry_report` 取成稿 PDF →
成文:景气度结论+趋势拆解(六维符号)+模型偏好标的+历史快照对比。

**个股解读**:`search_assets`(解析 asset_code)→ `get_company_tracking(公司名)`
→ 需要跨期对比时传 `report_date` 取历史期 → 成文:基本面跟踪要点+跨期变化,
模型打分参考 `get_model_picks`。

**深度专题报告**:`submit_deep_research(question, mode="plus")` → 等待期间用
data 工具取相关行业/标的客观数据 → 轮询拿到研究结论 → 综合成文(研究观点注明
来自 ADAMAS 研究引擎,数据佐证标 as_of,交叉验证部分是你自己的)。

**晨会纪要一页**:`get_industry_scores()`(全量,取分数最高/变动明显的 3-5 个)+
`get_model_picks(top_n=10)` → 一页式:今日景气度看点+模型偏好+风险提示+免责。
