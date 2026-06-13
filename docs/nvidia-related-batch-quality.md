# NVIDIA 相关上市公司批量新增质量记录

本批次使用 `scripts/research_pipeline.py` 先生成 SEC 草稿，再由 `scripts/add_nvidia_related_batch.py` 合并人工维护的 NVIDIA 关系映射，生成正式页面 JSON。

## 范围

已新增的美股/ADR 公司：

- 上游制造与设备：TSM、ASML、AMAT、LRCX、KLAC、AMKR
- AI 服务器与企业基础设施：SMCI、DELL、HPE
- 云与 GPU 云客户：MSFT、AMZN、GOOGL、ORCL、CRWV

已给现有公司增加标签：

- NVDA、MU 增加 `英伟达相关`

暂未纳入：

- 台股、韩股、日股、港股等非美股标的，例如台股 2330、三星电子、SK 海力士、鸿海、广达等。当前页面顶层公司模型只支持 `US/CN`，因此先不把非美股公司作为独立公司页加入；它们仍可作为供应链实体出现在关系图中。

## 自动化覆盖

- SEC ticker/CIK 解析
- SEC submissions 最近 filings
- SEC companyfacts 财务项
- `us-gaap` 与 `ifrs-full` 双 taxonomy
- USD、EUR、TWD、CNY 报告币种保留
- 年度收入、净利润/亏损、资产趋势
- 总收入历史构成，占比 100%
- NVIDIA 相关供应链/下游关系的上市代码和行情链接

## 人工复核与质量处理

- TSM 和 ASML 是外国发行人/ADR，已修正流水线以读取 IFRS 或非 USD 单位；TSM 保留 TWD，ASML 保留 EUR。
- GOOGL 等公司存在多个收入概念，已将脚本改为选择同类概念中最新可用事实，避免命中过时概念。
- KLAC 的部分 SEC XBRL 经营利润/毛利概念仍停留在旧年份，本批次正式 JSON 不采用这些陈旧字段。
- 收入构成没有自动拆分业务分部；为了避免错误数值，当前仅使用可核对的总收入历史，分部收入需后续逐家公司读取年报表格。

## 与手工新增的质量差异

- 优点：新增速度快，财务数值和 filings 可统一追溯到 SEC，结构一致，适合批量扩展 watchlist。
- 不足：业务分部、供应商比例、客户集中度和最新公司新闻仍依赖后续人工阅读年报、公告和公司新闻稿。
- 当前定位：可作为“可查询的初版公司页”，但不等同于 NVDA、MU 这种已手工深挖的完整专题页。
