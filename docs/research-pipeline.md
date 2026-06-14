# 公司研究流水线

本文记录批量新增或更新上市公司数据的半自动流程。目标是减少手动爬取和筛选的重复劳动，同时保留人工复核，避免把未经确认的供应链关系直接发布到页面。

## 设计原则

- 正式页面仍读取静态 JSON：`public/data/companies/*.json` 是唯一发布数据源。
- 自动化先生成候选稿：`research/drafts/*.draft.json` 只作为 review artifact，不直接覆盖正式公司数据。
- 官方来源优先：美股优先 SEC EDGAR；A 股优先巨潮资讯、上交所、深交所、北交所公告。
- 结构化数据优先：财务指标先用 XBRL/API/表格，再考虑 PDF 文本抽取。
- 供应链谨慎处理：客户、供应商、原材料溯源必须保留来源、关系描述和置信度。

## 数据源分层

| 市场 | 主数据源 | 适合自动化的内容 | 仍需复核的内容 |
| --- | --- | --- | --- |
| 美股 | SEC EDGAR `company_tickers`、`submissions`、`companyfacts` | ticker/CIK、10-K/10-Q/8-K、标准 XBRL 财务指标、财年/财季趋势 | 业务分部口径、客户/供应商关系、原材料溯源、中英文投资逻辑 |
| A 股 | 巨潮资讯、上交所、深交所、北交所公告；东方财富公告索引作候选发现 fallback | 公告发现、年报/季报/临时公告链接、公告类型分类 | PDF 表格抽取、前五大客户/供应商、上市公司映射、英文翻译、最终公告源回链 |
| 补充 | AKShare、Tushare、yfinance、公司官网/RSS | 行情、摘要字段、新闻入口、快速交叉检查 | 最终事实归因、授权/条款风险、供应链关系判断 |

## 当前脚本

```bash
python3 scripts/research_pipeline.py --plan-only
python3 scripts/research_pipeline.py --watchlist config/research-watchlist.json --output research/drafts
python3 scripts/research_pipeline.py --target MSFT --market US --output research/drafts
python3 scripts/research_pipeline.py --target 600519 --market CN --exchange SSE --output research/drafts
```

脚本会：

- 对美股：解析 SEC ticker map，拉取 submissions 和 companyfacts，生成最近 filings 与标准财务概念候选；ADR/外国发行人会同时检查 `us-gaap` 与 `ifrs-full`，并保留 SEC XBRL 中披露的报告币种（例如 EUR、TWD），不在流水线内做汇率换算。
- 对美股季度指标：只保留带 `CYxxxxQx` 或 `CYxxxxQxI` frame 的单季度/期末候选，避免把无 frame 的年初至今值误作单季度。
- 对 A 股：查询巨潮公告，初步分类年报、季报、分红、异常波动、投资者关系记录等公告。
- 当巨潮查询无结果时，对 A 股使用东方财富公告索引做候选发现；正式数据落库前应优先回链交易所或公告 PDF。
- 输出候选稿：`research/drafts/<market>-<ticker>.draft.json`。
- 记录失败：如果部分公司抓取失败，会写入 `research/drafts/research-failures.json`。

## Review 到正式数据

1. 运行 draft 生成脚本。
2. 打开候选 JSON，确认基础信息、公告链接和财务指标。
3. 从年报/季报中补齐：
   - 主营业务和业务分部；
   - 财务 highlights、trends、revenueMix、revenueMixHistory；
   - 供应商、供应商上游、原材料；
   - 下游客户和对应上市代码；
   - 公司级主题暴露 `themeExposure` 与实体级关系强度 `relationshipStrength`；
   - 最新动态与影响判断。
4. 写入或更新 `public/data/companies/<id>.json`。
5. 运行校验和构建：

```bash
python3 scripts/apply_relationship_strength.py
python3 scripts/build_company_index.py
python3 scripts/validate_data.py
npm run sync:pages
```

批量新增的专项质量记录：

- [SpaceX IPO 主题批量新增质量记录](./spacex-ipo-batch-quality.md)
- [NVIDIA 相关上市公司批量新增质量记录](./nvidia-related-batch-quality.md)
- [产业链关系强度评分](./relationship-strength-scoring.md)

## 定时任务状态

目前只保留手动触发，不启用 cron。相关 workflow 中会保留注释形式的 schedule 示例，等页面和数据质量流程稳定后再启用。

建议的未来频率：

- 12 小时：官方公告和新闻候选。
- 每日：SEC filings、A 股公告、财务公告候选。
- 每周：供应链、客户/供应商、业务描述和原材料溯源候选。

启用前需要补齐：

- 数据源限速与失败重试策略；
- draft 到正式 JSON 的人工 review checklist；
- 对供应链关系的置信度规则；
- GitHub Action artifact 或 PR review 机制；
- 需要账号的商业/社区数据源密钥管理。
