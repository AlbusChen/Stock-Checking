# A-share Volume Breakout Pipeline

## 目标 / Goal

新增一个独立的“放量突破”板块，用于每天扫描 A 股中满足量价突破口径的股票，并在页面中提供 20 / 60 / 120 日窗口切换。

The standalone breakout board scans A-share names daily and lets the UI switch across 20 / 60 / 120 trading-day windows.

## 数据来源 / Data Sources

- 全市场行情列表：东方财富 `push2delay` 延迟行情公开接口。
- 历史日 K：优先使用 Yahoo Finance A 股 `.SS` / `.SZ` 历史行情；如果 Yahoo 不可用，脚本会回退到东方财富 `push2his`。
- 同花顺可作为功能参照，但本项目不复制同花顺的展示文本；原因分析由脚本按公开量价字段生成。

The board uses Eastmoney delayed quote lists plus Yahoo Finance A-share historical candles. Tonghuashun can be used as product/function reference, but the generated analysis is our own rule-based interpretation.

## 当前筛选口径 / Current Criteria

- 交易范围：东方财富沪深 A 股集合，包括沪深主板、创业板、科创板。
- 突破定义：当日收盘价高于所选窗口的前高。
- 最低窗口放量：当日成交量不低于所选窗口均量的 `1.8x`。
- 列表预过滤量比：东方财富列表量比不低于 `1.5x`，用于减少历史 K 请求量。
- 最低成交额：`5000 万元`。
- 最低换手率：`1.0%`。
- 排除：ST / *ST，以及行情字段缺失的股票。

The script writes all qualified stocks under the above criteria to `public/data/volume-breakouts.json`.

## 原因分析 / Analysis Logic

每只股票的原因分析由以下因素组成：

- 价格位置：收盘价与窗口前高的差距。
- 放量程度：当日成交量与窗口均量的比值。
- 资金活跃度：成交额和换手率。
- 板块背景：东方财富行业与地域字段。

这类解释是“量价原因”，不是已核验的公告、新闻或基本面利好。后续如果要做新闻因果，可以追加公告/新闻源，再把原因分成“量价确认”和“消息催化”两栏。

## 更新任务 / Update Job

Workflow: `.github/workflows/update-volume-breakouts.yml`

- 手动触发：`workflow_dispatch`
- 定时触发：周一至周五 `09:30 UTC`，即中国/新加坡时间 `17:30`
- 输出：`public/data/volume-breakouts.json`
- 生成成功并检测到数据变化后，workflow 会提交数据文件；推送到 `main` 后触发现有 Pages 部署。

## 已知限制 / Known Limits

- 当前范围优先覆盖沪深 A 股。北交所接口在本地验证时不稳定，暂未纳入全量扫描。
- Yahoo Finance 的 A 股历史线可能比交易所收盘数据有延迟，因此页面显示的是“最新可用交易日”，而不强行写成系统当天日期。
- 原因分析目前基于行情数据和行业字段，不读取或复述第三方平台的个股解释。
