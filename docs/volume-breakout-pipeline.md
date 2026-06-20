# A-share Volume Breakout Pipeline

## 目标 / Goal

新增一个独立的“放量突破”板块，用于每天扫描 A 股中满足量价突破口径的股票，并在页面中提供 1 / 2 / 3 / 20 / 60 / 120 日窗口切换。

The standalone breakout board scans A-share names daily and lets the UI switch across 1 / 2 / 3 / 20 / 60 / 120 trading-day windows.

## 数据来源 / Data Sources

- 候选股票：默认 `hybrid` 模式会优先查询同花顺问财，例如 `今日放量突破`、`今日2日放量突破`、`今日3日放量突破`、`今日20日放量突破`、`今日60日放量突破`、`今日120日放量突破`。
- 全市场行情列表：东方财富 `push2delay` 延迟行情公开接口。
- 历史日 K：优先使用 Yahoo Finance A 股 `.SS` / `.SZ` 历史行情；如果 Yahoo 不可用，脚本会回退到东方财富 `push2his`。
- 基本面/消息催化：东方财富公告接口与东方财富资讯搜索接口，按股票名/代码抓取近 30 天公开标题与摘要。
- 同花顺/问财只用于候选名单与公开标签线索；本项目不复制同花顺解释文本，最终入选仍由脚本按统一量价口径复核。

The default `hybrid` mode uses Tonghuashun iWencai for candidate names and public tags, then re-validates every name with Eastmoney quotes and Yahoo/Eastmoney daily candles. Generated analysis remains our own rule-based interpretation.

## 当前筛选口径 / Current Criteria

- 交易范围：东方财富沪深 A 股集合，包括沪深主板、创业板、科创板。
- 候选集合：默认优先使用同花顺问财候选；若问财不可用或候选行情补全失败，回退到本项目全市场量价预筛。
- 突破定义：当日收盘价高于所选窗口的前高。
- 自选窗口：1 / 2 / 3 日用于超短线观察，20 / 60 / 120 日用于短线、中线和中长期观察。
- 最低窗口放量：当日成交量不低于所选窗口均量的 `1.8x`。
- 列表预过滤量比：东方财富列表量比不低于 `1.5x`，用于减少历史 K 请求量。
- 最低成交额：`5000 万元`。
- 最低换手率：`1.0%`。
- 排除：ST / *ST，以及行情字段缺失的股票。

The script writes all qualified stocks under the above criteria to `public/data/volume-breakouts.json`.

## 原因分析 / Analysis Logic

每只股票的分析拆成两层，避免把技术形态误写成上涨原因：

- 量价确认：价格位置、放量程度、成交额、换手率，用于解释为什么入选“放量突破”。
- 基本面/消息催化：近 30 天公告和资讯标题会被归类为订单/中标、产品涨价/供需紧张、业绩改善、并购重组、政策/产业主题、产能/产品进展、资本动作、监管/风险事件或交易性报道。
- 产业核验方向：当公告/新闻不足时，会根据行业字段提示应重点核验的方向，例如原材料涨价/短缺、客户认证、设备订单、创新药进展等。
- 候选线索：若命中同花顺问财，会展示问财候选来源和公开标签，但不把第三方解释文本当作结论。

公告/新闻催化只表示“可回溯的核验线索”，不单独证明当天上涨因果；若只找到龙虎榜、成交额、涨停等交易性报道，页面会明确标成非强基本面催化。

## 更新任务 / Update Job

Workflow: `.github/workflows/update-volume-breakouts.yml`

- 手动触发：`workflow_dispatch`
- 定时触发：周一至周五 `09:30 UTC`，即中国/新加坡时间 `17:30`
- 输出：`public/data/volume-breakouts.json`
- 生成成功并检测到数据变化后，workflow 会提交数据文件；推送到 `main` 后触发现有 Pages 部署。
- workflow 会尝试安装 `pywencai==0.13.1` 来启用同花顺问财候选源；安装或问财查询失败时，脚本会回退到本项目量价预筛，不中断日更。

## 已知限制 / Known Limits

- 当前范围优先覆盖沪深 A 股。北交所接口在本地验证时不稳定，暂未纳入全量扫描。
- 同花顺问财没有稳定的官方开放 API，可能受 cookie、反爬或访问频率影响；因此它只作为候选增强源，不作为唯一数据源。
- Yahoo Finance 的 A 股历史线可能比交易所收盘数据有延迟，因此页面显示的是“最新可用交易日”，而不强行写成系统当天日期。
- 公告/新闻分析基于标题和短摘要做规则分类，不读取或复述第三方长文本解释；没有可靠基本面线索时会显示“继续核验”，而不是强行编造利好。
