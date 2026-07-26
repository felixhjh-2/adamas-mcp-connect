# CHANGELOG

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
