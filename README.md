# Stock Checking

一个面向 GitHub Pages 的上市公司公开信息查询站。当前首批覆盖 `AAPL`、`NVDA`、`INTC`，数据保存在 `public/data`，页面在浏览器端读取静态 JSON。

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

- `scripts/update_news.py`：每 12 小时抓取配置的 RSS 动态。
- `scripts/update_sec_filings.py`：刷新 SEC 10-K、10-Q、8-K 链接。
- `scripts/build_company_index.py`：根据公司 JSON 生成搜索索引。
- `scripts/validate_data.py`：校验数据结构和来源引用。

GitHub Actions 已包含：

- `Deploy GitHub Pages`：main 分支构建并发布 Pages。
- `Refresh News`：每 12 小时刷新新闻与 SEC 元数据。
- `Weekly Research Refresh`：每周刷新较低频研究元数据。

## 扩展公司

新增公司时，在 `public/data/companies` 下添加一个公司 JSON，然后运行：

```bash
python3 scripts/build_company_index.py
python3 scripts/validate_data.py
npm run sync:pages
```

A 股数据模型已预留 `market: "CN"`，后续可接入巨潮资讯、上交所、深交所公告和公司年报。
