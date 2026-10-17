---
name: adamas-research-report
description: 用 ADAMAS 投研数据写研究报告/晨会纪要/行业跟踪/全球宏观对比，并在网页知识库新建、续问或重新生成回答。当用户要做投研分析或知识库问答，且已接入 ADAMAS MCP 连接器时使用。
---

# ADAMAS 投研报告技能

前提:已在连接器中接入 ADAMAS MCP(工具名以 `list_capabilities`、`get_industry_scores` 等出现)。

接入材料（2.6.5，2026-10-18）：本技能只使用标准档 28 个工具。先发现当前端点能力，不要假定当前 key 未获授权的工具可用。

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
     `submit_notes_report`(深度纪要成稿,异步)、
     `submit_company_roundtable`(指定公司与报告期数的横向研究,异步)、
     `submit_kb_question`(原生网页知识库新建/续问)、`regenerate_kb_answer`(最新回答重新生成)。
     提交后按返回的 `next_step` 轮询 `get_research_task`,等待期间先取客观数据并起草框架;
     ⚠️ 这六个会**消耗所属账号的使用额度**(客观数据类不消耗):
     · 同一个业务不要反复提交；确认失败后按服务端结算结果处理，状态未知不代表失败或已退款，成功产出的不退;
     · `submit_deep_research` / `submit_kb_question` / `regenerate_kb_answer` 选 `mode="pro"` 用量按 2 倍计,按需要选档而不是默认拉满;
     · 若返回"该 API key 未绑定用户",说明这把 key 还没绑账号,联系 ADAMAS 处理,重试无用。
4. **额度与恢复先自查**:批量调用或提交前用 `get_my_quota`(免日扣减，仍计 RPM)；提交回执丢失先用 `list_my_research_tasks` 恢复 task_id，再轮询，不能直接重复付费提交。历史支持 limit/status/kind/cursor，翻页保留原筛选；只读落库摘要，不代表上游最新状态。
   六个付费提交工具支持可选 `idem_key`：非空须 ≤128 个 ASCII 字符，匹配 `[A-Za-z0-9][A-Za-z0-9_.:-]*`。同一 API key、同一工具内，同键与完整业务参数一致时返回原任务、不重复扣本次账号用量；深研 `session_id` 也纳入业务参数。换参冲突为 `BadParam`，新业务用新键；新键不等于恢复原任务。无键兼容每次 RPC 新建意图，但回执与本版本创建任务的轮询会返回生成的 `auto:<UUIDhex>` 恢复键。丢回执先历史找 task_id，再轮询取键；需要恢复提交时，向同一工具显式传返回键与完整原参数。继续传空键仍是新意图，轮询不会自动重新派发付费任务。`idempotency_persisted:true` 表示提交意图已记录，受理可能待确认；先查历史/轮询，不盲重投，不推断已退款。按可选 `task_status` 与 `progress` 查看原任务提示，当前结果仍用轮询获取。
5. **错误按恢复指引处理**:检查 `isError`、`error_class` 与 `recovery.action`，仅 `retry_safe=true` 才自动重放；按可选 `retry_after_seconds` 等待，不盲重试。
6. **长文本先检查整次请求大小**：`POST /mcp` 的完整 UTF-8 JSON-RPC 请求体（协议字段及全部参数）最多 **1 MiB（1048576 bytes）**；查看 `list_capabilities().transport.request_limits`。字段字符上限不等于完整请求字节上限，中文、emoji、JSON 转义和空白都计入实际传输字节。超限返回 HTTP 413，本次请求未进入工具业务；不能据此推断此前受理状态未知的提交未被受理，先核对原任务或原资源。不自动截断文本、丢弃 history 或 versions，也不换键重投写入或收费操作。大文本可用网页编辑，或由用户明确缩小输入范围后再操作。
   编辑消息时，`changes.versions` 最多20项，每项≤399996个Unicode字符；完整数组按 `json.dumps(versions, ensure_ascii=False)` 默认格式序列化后≤400000个Unicode字符，含括号、引号、转义、逗号和空格。非ASCII字符不转义，元素之间用逗号加一个空格分隔。这些字段限制同时生效，仍须满足完整 UTF-8 JSON-RPC 请求体的 1 MiB 上限；不能只检查单项正文长度。

## 成文规范(必须遵守)

- 引用数字时保留工具明确提供的数据日期（若提供），不要把来源日期推成所有相关事实的数据截止日；日期未提供时说明未知，不编造日期。
- 区分三种内容并让读者能分辨:①ADAMAS 客观数据 ②ADAMAS 模型观点(深度研究/选股/景气度打分)
  ③你自己的推断与综合;
- 报告结尾**原文保留**工具返回中的 disclaimer(免责声明),一字不改;
- 六维趋势符号含义:↗ 改善 / → 持平 / ↘ 恶化(维度:当前/预期/供给/成本/竞争/出口)。

- 公司正文先检查 `meta.content_status`：`complete` 才是本次完整交付，`truncated` 仅为部分正文，`omitted` / `unavailable` 不代表读过全文。全文错误保留目录，不能据目录编造正文。
- 信息流先检查 `availability` / `stale`；`as_of` 与 `source_updated_at` 来自文件 mtime，不是逐条事件日期。旧文件标明旧日期，not_generated 的空列表不代表市场没有新闻。
- 保留研究正文已有的 `[E1]`、`[W1]` 等标记与原文免责声明。E 编号只对照 `doc_id_mapping` 中可用的安全文档标识与来源日期（若提供）；来源日期不自动等于相关事实的数据截止日。映射是检索证据标识，不是逐条结论的出处核验。
- W 编号仅指本轮联网补充条目，不代表已定位原始网页、已核实 URL 或可访问链接；没有对应来源信息就说明限制，不补造网页标题或链接。
- 按 `citation_note` 使用来源信息；`doc_id_mapping` 可能为空或缺少对应项，正文也可能没有引用标记。保留原标记并说明引用信息有限，不替答案补贴编号或臆造结论与来源的对应关系；`evidence_count` / `web_evidence_count` 不等于可追溯引用数量，不宣称全部回答均有出处。
- 核对数字时同时核对主体、期间、单位与分母，近似比例不能扩写为更精确的数值。保留原摘录的“可能”等限定及候选原因；推导须说明条件。来源数字冲突时明确列出差异并待核验，不能仅按报告日期、来源数量或取平均消除冲突。缺少原摘录的抽取摘要及经过清洗的文本不能称为已完成原文核验。

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


**指定公司横向研究**：先 `search_assets` 确认代码，再 `check_company_coverage` 检查报告覆盖，
调用 `submit_company_roundtable(asset_codes=[...], question=..., periods=1)`；最多10家公司、
每家最近1–3期，可显式传入已完成问答 history。保留完整参数与 idem_key，用
`get_research_task` 读取回答及本次实际公司/报告日期来源，不把通用深研当作这条流程。

**网页知识库资料管理**：先 `list_kb_conversations`，再 `get_kb_conversation` 分页读取完整消息。
网页 conversation_id/message_id 与研究 task_id/session_id 不同；深研不会自动创建网页会话。
用户明确要求时可 `update_kb_message` 编辑，或 `delete_kb_conversation(confirm_delete=true)` 删除。
公开分享使用 `share_kb_content(make_public=true)`，任何持链接者均可免登录阅读，必须先获得
用户明确公开意图；超时先查 `manage_kb_shares`，不重复发新链接。删除会话不撤销独立分享快照，
需按分享ID显式 revoke。

**原生知识库提问与重新生成**：用户要在网页继续的会话时使用 `submit_kb_question(question, conversation_id=0)` 新建，或传本人未删除 conversation_id 续问。服务采用本人最近 3 轮已结束且有正文的问答摘要（包括保留的部分回答；问题至 2000、回答至 500 个 Unicode 字符），不改写原正文；调用方不传 history/session_id，网页后续也连续使用同一会话历史。`regenerate_kb_answer(message_id=...)` 仅重做最新已结束助手消息，用其原问题并排除目标回答的历史。保留原 task_id / generation_id / conversation_id / message_id，用原任务轮询，二者消耗 research 提交额度及账号用量，pro 模式按 2 倍。

重新生成保留原 content / agent_steps / 完整 versions；没有新回答时原样回退，有部分新回答则保留为新版本并计入用量，网页显示最近 5 版。以 completion / partial 判断完整度。显式 `get_research_task(include_original_native=true)` 只读取原快照供核对及恢复所需数据；读取不自动恢复，也不重跑或再次结算。
原快照按体量读取：原快照JSON≤262144 bytes的小对象返回 original_native_snapshot；大对象返回 original_native_snapshot_chunk。首请求 original_native_offset=0，后续仅在 include_original_native=true 时传上一页 next_offset（UTF-8 字节偏移），直到 next_offset=null。每页原始bytes最多262144，小对象只接受offset=0，offset达到或超过total_bytes返回BadParam。逐页 base64 解码为 bytes，按 chunk_offset 拼接，核对 total_bytes 与 snapshot_sha256 后，才一次 UTF-8 解码并 JSON 解析；不能逐页先解码 UTF-8，分片可能切在 emoji 字节中间。每页重新校验原 key 与账号权限，且应核对同一 recovery_snapshot_id / 消息 / 会话 / SHA / 总字节数；页外 versions_trimmed 可随任务终态变化，不是原快照 JSON 的一部分。
快照 versions 保留完整原字符串及字节数；非空且合法时再解析其中的 JSON，不自动修复或丢弃旧数据。`update_kb_message` 只能显式编辑 content / versions，不能恢复 agent_steps。删除会话不会抹去独立回执/原快照，读取快照不会重建已删除会话；活动生成先停止并确认终态再编辑或删除。

基于检索材料的知识库回答先核对材料与结论再显示正文，首字等待可能延长。等待时查原任务，不换键重投；核对未通过不视作完整交付，也不能把暂时无正文当作已失败或已退款。用户可按原轮请求停止，最终仍查原任务确认。

使用 MCP 知识库提问、重新生成或深度研究时，保留返回答复对原摘录、条件计算和待核验口径的区分。不要把近似数扩写为精确数，把候选原因改成确定因果，或用其他指标补齐未建立的年份、期间、分母。算术相容不能替代原口径核实。

**停止知识库生成**：原生 MCP 任务使用 `stop_kb_generation(message_id=..., generation_id=原本轮UUID)`；旧网页流可省略 generation_id。不能拿旧轮次停止新一轮。`cancel_requested` 后查询原任务确认终态，`not_running` 表示该轮不在运行，`not_cancellable_here` 不证明已停止。停止不等于退款，部分新回答仍计入用量；它不取消普通深研或通用 AI 异步任务，不请求退款。

指定原轮停止被旧服务拒绝时，保留原 generation_id 并查询原任务；不要省略 generation_id 降级为消息级停止，也不要换成后续轮次的标识。等待服务更新或联系支持，拒绝不证明该轮已停止。

原生知识库完成结果的可选 `query` 返回站点保存的原问题，重新生成沿用该轮问题；旧后端可能为空。不要从回答正文猜测原问题。

研究结果的 `meta` 可选带 `citable_count`（本轮作答映射的本地证据编号数）与 `dropped_uncitable_count`（进入作答前因缺少安全来源而排除的检索项数），仅返回非负整数。旧结果可缺省；两者不保证相加等于检索总量，统计不能代替逐条事实核验。

原生知识库的部分交付结果可保留本轮已收到的可选 `doc_id_mapping` 与证据统计。只核对该结果实际提供的 E 编号；旧服务、历史任务或来源不足时映射仍可能为空。来源映射不表示回答完整、停止成功或已退款，缺少对应项时不能宣称来源已核验。

客户端可能缓存工具列表；看不到新工具时刷新工具列表或断开后重新连接，再检查 tools/list。接入材料 2.6.5 与服务 contract_version `2026-10-14.2` 分别标识材料和服务契约。

**热点纪要历史**：`get_hot_notes(date="YYYY-MM-DD")` 按日期分页，继续使用 next_cursor；
`get_hot_notes(note_id=...)` 读取段落正文，不能同时带日期/游标。
它与最新信息流和新生成研究纪要不同，历史内容需标明日期。
