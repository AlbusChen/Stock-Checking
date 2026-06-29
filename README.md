# Stock Checking

一个面向 GitHub Pages 的上市公司公开信息查询站。当前数据覆盖美股、A 股及产业链主题公司，正式页面数据保存在 `public/data`，浏览器端读取静态 JSON。

页面重点不只是展示公司资料，也会按“产业链卡点 -> 相关上市公司 -> 证据等级 -> 判断失效信号”的方式组织研究结论。核心数据字段包括：

- `themeExposure`：公司与主题的相关性。
- `relationshipStrength`：供应链实体与目标公司的关系强度。
- `sources[].evidenceLevel`：来源证据等级，分为 `strong`、`medium`、`weak`、`needs-checking`。
- `supplyChain.scarceLayers`：产业链稀缺层和优先研究顺序。
- `failureConditions`：哪些信号出现时，说明当前判断需要重新评估。

## 本地运行

```bash
npm install
npm run dev
```

## 构建与校验

```bash
npm run validate:data
npm run build
```

## 数据更新

- `scripts/research_pipeline.py`：从 SEC EDGAR、巨潮公告等来源生成公司研究候选稿，不直接覆盖正式页面数据。
- `scripts/update_news.py`：每 12 小时抓取配置的 RSS 动态。
- `scripts/apply_bilingual_fields.py`：为指标、新闻、供应链展示字段补齐中英文字段。
- `scripts/update_sec_filings.py`：刷新 SEC 10-K、10-Q、8-K 链接。
- `scripts/build_company_index.py`：根据公司 JSON 生成搜索索引。
- `scripts/validate_data.py`：校验数据结构、来源引用、证据等级、卡点层和 5 分关系的强证据约束。

GitHub Actions 已包含：

- `Deploy GitHub Pages`：main 分支构建并发布 Pages。
- `Generate Research Drafts`：手动生成批量公司研究候选稿；定时触发暂未启用。
- `Refresh News`：手动刷新新闻与 SEC 元数据；定时触发暂未启用。
- `Update Volume Breakouts`：A 股放量突破板块，当前启用工作日收盘后的定时任务。
- `Weekly Research Refresh`：手动刷新较低频研究元数据；定时触发暂未启用。

公司研究页面上的低频/高频更新频率目前仍是目标设计说明。除放量突破板块外，公司研究、新闻和周度研究自动定时更新会等页面和数据结构进一步完善后再启用。

## 扩展公司

新增公司时，在 `public/data/companies` 下添加一个公司 JSON，然后运行：

```bash
python3 scripts/build_company_index.py
python3 scripts/apply_bilingual_fields.py
python3 scripts/validate_data.py
npm run sync:pages
```

A 股数据模型已预留 `market: "CN"`，后续可接入巨潮资讯、上交所、深交所公告和公司年报。

新增或批量更新时，需要特别检查：

- 5 分关系必须有至少一个强证据来源。
- 新闻和市场报道可以作为线索，但不能单独支撑核心瓶颈。
- 下游客户通常不能因为“买了产品”就被打成高相关，除非有直接收入、合同、产能或技术约束证据。
- 每个核心卡点都需要写清楚判断失效信号，避免只给单向利好叙事。

批量新增或更新公司时，先生成候选稿：

```bash
npm run research:plan
npm run research:draft
```

详细流程记录见 [docs/research-pipeline.md](docs/research-pipeline.md) 和 [docs/relationship-strength-scoring.md](docs/relationship-strength-scoring.md)。
