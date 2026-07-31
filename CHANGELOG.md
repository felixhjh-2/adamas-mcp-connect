# CHANGELOG

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
