# ADAMAS MCP — 接入仓库

> 把 ADAMAS 投研能力接进你自己的 AI:产业景气度、产业链传导图谱、公司跟踪、模型选股、
> 每日信息流、深度研究与纪要生成 —— **一个 MCP 端点,13 个工具**。

- **端点**:`https://www.adamas-research.com/mcp`(remote MCP,streamable HTTP,无需安装任何服务)
- **认证**:`Authorization: Bearer <your-api-key>` —— API key 向 ADAMAS 团队申请
- **完整文档**:[docs/USAGE.md](docs/USAGE.md)(全部工具的参数/返回/示例/配额/FAQ)

> 本仓库只包含接入材料(文档 / Skill / 示例),服务本体由 ADAMAS 托管运行。
> 没有 API key 时以下配置可以先填好,拿到 key 即刻生效。

## 30 秒接入

### WorkBuddy(腾讯)

设置 → 连接器 → 自定义连接器:

| 配置项 | 值 |
|---|---|
| 连接器类型 | MCP(streamable HTTP) |
| URL | `https://www.adamas-research.com/mcp` |
| 请求头 | `Authorization: Bearer <your-api-key>` |

建议同时导入配套 Skill(见下文「安装 Skill」),让你的 agent 按 ADAMAS 推荐的方法论用这些工具。

### Claude Code

```bash
claude mcp add adamas --transport http https://www.adamas-research.com/mcp \
  --header "Authorization: Bearer <your-api-key>"
```

或者用插件一步装齐(MCP 连接 + Skill 方法论一起装,key 走环境变量):

```bash
export ADAMAS_API_KEY=<your-api-key>          # 建议写进 shell profile
claude  # 会话内执行:
#   /plugin marketplace add felixhjh-2/adamas-mcp-connect
#   /plugin install adamas-research-report@adamas
```

### Claude Desktop / Cursor / Codex 等(通用 JSON 配置)

```json
{
  "mcpServers": {
    "adamas": {
      "type": "http",
      "url": "https://www.adamas-research.com/mcp",
      "headers": { "Authorization": "Bearer <your-api-key>" }
    }
  }
}
```

### 自建 agent(Python)

见 [examples/quickstart.py](examples/quickstart.py):

```bash
pip install mcp
ADAMAS_API_KEY=<your-api-key> python examples/quickstart.py
```

## 能做什么(13 个工具速览)

| 能力域 | 工具 |
|---|---|
| 资产解析 | `search_assets`(名称/代码 → 标准信息+行业分类) |
| 产业 | `get_industry_scores`(景气度+六维趋势)`get_industry_graph`(产业链传导图谱)`get_industry_report`(报告 PDF) |
| 公司 | `get_company_tracking`(跟踪报告全文,含历史期) |
| 选股 | `get_model_picks`(最新一期模型排名)`submit_stock_screen`(产业链选股,异步) |
| 信息流 | `get_info_feed`(当日要闻打分摘要) |
| 研究成稿 | `submit_deep_research`(深度研究问答,异步)`submit_notes_report`(深度纪要+PDF,异步)`get_strategy_reports`(沙盘推演报告) |
| 入口 | `list_capabilities`(能力地图,每个会话第一站)`get_research_task`(异步任务轮询) |

典型玩法:让你的 AI 写行业跟踪简报、盘前扫当日高分要闻、推演产业链传导、
把研究问题外包给 ADAMAS 研究引擎、一键产出深度纪要 PDF。方法论详见 Skill。

## 安装 Skill(可选,强烈推荐)

Skill 是「怎么用好这些工具」的方法论包:先看地图再取数、标的先解析代码、
数据与观点分开写、限流退避、成文规范(数据标注日期、免责声明原文保留)。

- **WorkBuddy / OpenClaw**:下载本仓库,把 `plugins/adamas-research-report/skills/adamas-research-report/`
  整个目录作为技能导入(技能管理 → 导入本地技能包);
- **Claude Code**:上面的插件方式自动装;或手动拷贝该目录到项目 `.claude/skills/`;
- **其他 Agent 框架**:把该目录放进框架的 skills 目录即可(触发条件写在 SKILL.md frontmatter)。

## 申请 API key / 提额 / 支持

联系 ADAMAS 团队。key 按账号发放,支持有效期与配额管理。遇到问题先看 [docs/USAGE.md](docs/USAGE.md) 第 8 节 FAQ。

## 版本

见 [CHANGELOG.md](CHANGELOG.md)。文档与线上服务同步更新,以本仓库 main 为准。
