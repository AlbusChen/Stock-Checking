#!/usr/bin/env python3
"""Add curated historical financial trend data to company reports."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"
ACCESSED_AT = "2026-06-08"


def point(period: str, zh: str, value: float, source_ids: list[str] | None = None) -> dict:
    item = {
        "period": period,
        "periodZh": zh,
        "periodEn": period,
        "value": value,
    }
    if source_ids:
        item["sourceIds"] = source_ids
    return item


def segment(name: str, zh: str, revenue: float, total: float | None = None) -> dict:
    item = {
        "name": name,
        "nameZh": zh,
        "nameEn": name,
        "revenue": revenue,
        "unit": "USD billions",
    }
    if total:
        item["share"] = round(revenue / total * 100, 2)
    return item


def period(
    period_name: str,
    period_zh: str,
    total_revenue: float,
    source_ids: list[str],
    segments: list[dict],
    note: str | None = None,
    note_zh: str | None = None,
) -> dict:
    item = {
        "period": period_name,
        "periodZh": period_zh,
        "periodEn": period_name,
        "totalRevenue": total_revenue,
        "sourceIds": source_ids,
        "segments": segments,
    }
    if note and note_zh:
        item["note"] = note
        item["noteZh"] = note_zh
        item["noteEn"] = note
    return item


def sec_companyfacts_source(company_id: str, cik: str, name: str) -> dict:
    return {
        "id": f"{company_id}-sec-companyfacts",
        "title": f"{name} SEC Companyfacts XBRL data",
        "titleZh": f"{name} SEC Companyfacts XBRL 数据",
        "titleEn": f"{name} SEC Companyfacts XBRL data",
        "publisher": "SEC EDGAR",
        "url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        "accessedAt": ACCESSED_AT,
        "type": "sec",
    }


FINANCIAL_HISTORY = {
    "aapl": {
        "source": sec_companyfacts_source("aapl", "0000320193", "Apple"),
        "trends": [
            {
                "id": "quarterly-revenue",
                "label": "Quarterly revenue",
                "labelZh": "财季收入",
                "labelEn": "Quarterly revenue",
                "unit": "USD billions",
                "cadence": "quarterly",
                "note": "Q4 values are derived from full-year net sales minus the first three reported quarters.",
                "noteZh": "第四财季数值由全年净销售额减前三个已披露财季推得。",
                "noteEn": "Q4 values are derived from full-year net sales minus the first three reported quarters.",
                "sourceIds": ["aapl-sec-companyfacts", "aapl-q2-2026", "aapl-10k-2025"],
                "points": [
                    point("Q1 FY2025", "25财年Q1", 124.300),
                    point("Q2 FY2025", "25财年Q2", 95.359),
                    point("Q3 FY2025", "25财年Q3", 94.036),
                    point("Q4 FY2025", "25财年Q4", 102.466, ["aapl-10k-2025"]),
                    point("Q1 FY2026", "26财年Q1", 143.756),
                    point("Q2 FY2026", "26财年Q2", 111.184, ["aapl-q2-2026"]),
                ],
            },
            {
                "id": "quarterly-gaap-gross-margin",
                "label": "Quarterly GAAP gross margin",
                "labelZh": "财季 GAAP 毛利率",
                "labelEn": "Quarterly GAAP gross margin",
                "unit": "percent",
                "cadence": "quarterly",
                "note": "Gross margin is gross profit divided by net sales.",
                "noteZh": "毛利率按毛利除以净销售额计算。",
                "noteEn": "Gross margin is gross profit divided by net sales.",
                "sourceIds": ["aapl-sec-companyfacts", "aapl-q2-2026", "aapl-10k-2025"],
                "points": [
                    point("Q1 FY2025", "25财年Q1", 46.88),
                    point("Q2 FY2025", "25财年Q2", 47.05),
                    point("Q3 FY2025", "25财年Q3", 46.49),
                    point("Q4 FY2025", "25财年Q4", 47.18, ["aapl-10k-2025"]),
                    point("Q1 FY2026", "26财年Q1", 48.16),
                    point("Q2 FY2026", "26财年Q2", 49.27, ["aapl-q2-2026"]),
                ],
            },
            {
                "id": "annual-revenue",
                "label": "Annual net sales",
                "labelZh": "财年净销售额",
                "labelEn": "Annual net sales",
                "unit": "USD billions",
                "cadence": "annual",
                "note": "Annual net sales in USD billions.",
                "noteZh": "年度净销售额，单位为十亿美元。",
                "noteEn": "Annual net sales in USD billions.",
                "sourceIds": ["aapl-sec-companyfacts", "aapl-10k-2025"],
                "points": [
                    point("FY2021", "21财年", 365.817),
                    point("FY2022", "22财年", 394.328),
                    point("FY2023", "23财年", 383.285),
                    point("FY2024", "24财年", 391.035),
                    point("FY2025", "25财年", 416.161, ["aapl-10k-2025"]),
                ],
            },
        ],
        "revenueMixHistory": [
            period(
                "FY2023",
                "23财年",
                383.285,
                ["aapl-10k-2025"],
                [
                    segment("iPhone", "iPhone", 200.583, 383.285),
                    segment("Services", "服务", 85.200, 383.285),
                    segment("Mac", "Mac", 29.357, 383.285),
                    segment("iPad", "iPad", 28.300, 383.285),
                    segment("Wearables, Home and Accessories", "可穿戴、家居与配件", 39.845, 383.285),
                ],
                "Product and service category net sales from Apple Form 10-K.",
                "来自 Apple 10-K 的产品与服务类别净销售额。",
            ),
            period(
                "FY2024",
                "24财年",
                391.035,
                ["aapl-10k-2025"],
                [
                    segment("iPhone", "iPhone", 201.183, 391.035),
                    segment("Services", "服务", 96.169, 391.035),
                    segment("Mac", "Mac", 29.984, 391.035),
                    segment("iPad", "iPad", 26.694, 391.035),
                    segment("Wearables, Home and Accessories", "可穿戴、家居与配件", 37.005, 391.035),
                ],
            ),
            period(
                "FY2025",
                "25财年",
                416.161,
                ["aapl-10k-2025"],
                [
                    segment("iPhone", "iPhone", 209.586, 416.161),
                    segment("Services", "服务", 109.158, 416.161),
                    segment("Mac", "Mac", 33.708, 416.161),
                    segment("iPad", "iPad", 28.023, 416.161),
                    segment("Wearables, Home and Accessories", "可穿戴、家居与配件", 35.686, 416.161),
                ],
            ),
        ],
    },
    "nvda": {
        "source": sec_companyfacts_source("nvda", "0001045810", "NVIDIA"),
        "trends": [
            {
                "id": "quarterly-revenue",
                "label": "Quarterly revenue",
                "labelZh": "财季收入",
                "labelEn": "Quarterly revenue",
                "unit": "USD billions",
                "cadence": "quarterly",
                "note": "Q4 values are derived from full-year revenue minus the first three reported quarters.",
                "noteZh": "第四财季数值由全年收入减前三个已披露财季推得。",
                "noteEn": "Q4 values are derived from full-year revenue minus the first three reported quarters.",
                "sourceIds": ["nvda-sec-companyfacts", "nvda-q1-fy2027", "nvda-fy2026-results", "nvda-10k-2026"],
                "points": [
                    point("Q4 FY2025", "25财年Q4", 39.331, ["nvda-10k-2026"]),
                    point("Q1 FY2026", "26财年Q1", 44.062),
                    point("Q2 FY2026", "26财年Q2", 46.743),
                    point("Q3 FY2026", "26财年Q3", 57.006),
                    point("Q4 FY2026", "26财年Q4", 68.127, ["nvda-fy2026-results"]),
                    point("Q1 FY2027", "27财年Q1", 81.615, ["nvda-q1-fy2027"]),
                ],
            },
            {
                "id": "quarterly-gaap-gross-margin",
                "label": "Quarterly GAAP gross margin",
                "labelZh": "财季 GAAP 毛利率",
                "labelEn": "Quarterly GAAP gross margin",
                "unit": "percent",
                "cadence": "quarterly",
                "note": "Q1 FY2026 gross margin includes NVIDIA's H20-related charge impact.",
                "noteZh": "2026 财年第一财季毛利率包含 NVIDIA 披露的 H20 相关费用影响。",
                "noteEn": "Q1 FY2026 gross margin includes NVIDIA's H20-related charge impact.",
                "sourceIds": ["nvda-sec-companyfacts", "nvda-q1-fy2027", "nvda-fy2026-results", "nvda-10k-2026"],
                "points": [
                    point("Q4 FY2025", "25财年Q4", 73.04, ["nvda-10k-2026"]),
                    point("Q1 FY2026", "26财年Q1", 60.52),
                    point("Q2 FY2026", "26财年Q2", 72.43),
                    point("Q3 FY2026", "26财年Q3", 73.41),
                    point("Q4 FY2026", "26财年Q4", 75.00, ["nvda-fy2026-results"]),
                    point("Q1 FY2027", "27财年Q1", 74.93, ["nvda-q1-fy2027"]),
                ],
            },
            {
                "id": "annual-revenue",
                "label": "Annual revenue",
                "labelZh": "财年收入",
                "labelEn": "Annual revenue",
                "unit": "USD billions",
                "cadence": "annual",
                "note": "Annual revenue in USD billions.",
                "noteZh": "年度收入，单位为十亿美元。",
                "noteEn": "Annual revenue in USD billions.",
                "sourceIds": ["nvda-sec-companyfacts", "nvda-10k-2026"],
                "points": [
                    point("FY2022", "22财年", 26.914),
                    point("FY2023", "23财年", 26.974),
                    point("FY2024", "24财年", 60.922),
                    point("FY2025", "25财年", 130.497),
                    point("FY2026", "26财年", 215.938, ["nvda-10k-2026"]),
                ],
            },
        ],
        "revenueMixHistory": [
            period(
                "FY2024",
                "24财年",
                60.922,
                ["nvda-10k-2026"],
                [
                    segment("Data Center", "数据中心", 47.525, 60.922),
                    segment("Gaming / AI PC", "游戏 / AI PC", 10.447, 60.922),
                    segment("Professional Visualization", "专业可视化", 1.553, 60.922),
                    segment("Automotive", "汽车", 1.091, 60.922),
                    segment("OEM and Other", "OEM 与其他", 0.306, 60.922),
                ],
                "Historical mix uses NVIDIA's annual-report end-market categories.",
                "历史构成采用 NVIDIA 年报的终端市场分类口径。",
            ),
            period(
                "FY2025",
                "25财年",
                130.497,
                ["nvda-10k-2026"],
                [
                    segment("Data Center", "数据中心", 115.186, 130.497),
                    segment("Gaming / AI PC", "游戏 / AI PC", 11.350, 130.497),
                    segment("Professional Visualization", "专业可视化", 1.878, 130.497),
                    segment("Automotive", "汽车", 1.694, 130.497),
                    segment("OEM and Other", "OEM 与其他", 0.389, 130.497),
                ],
            ),
            period(
                "FY2026",
                "26财年",
                215.938,
                ["nvda-10k-2026", "nvda-fy2026-results"],
                [
                    segment("Data Center", "数据中心", 193.737, 215.938),
                    segment("Gaming / AI PC", "游戏 / AI PC", 16.042, 215.938),
                    segment("Professional Visualization", "专业可视化", 3.191, 215.938),
                    segment("Automotive", "汽车", 2.349, 215.938),
                    segment("OEM and Other", "OEM 与其他", 0.619, 215.938),
                ],
            ),
        ],
    },
    "intc": {
        "source": sec_companyfacts_source("intc", "0000050863", "Intel"),
        "trends": [
            {
                "id": "quarterly-revenue",
                "label": "Quarterly revenue",
                "labelZh": "季度收入",
                "labelEn": "Quarterly revenue",
                "unit": "USD billions",
                "cadence": "quarterly",
                "note": "Q4 values are derived from full-year revenue minus the first three reported quarters.",
                "noteZh": "第四季度数值由全年收入减前三个已披露季度推得。",
                "noteEn": "Q4 values are derived from full-year revenue minus the first three reported quarters.",
                "sourceIds": ["intc-sec-companyfacts", "intc-q1-2026", "intc-fy2025-results", "intc-10k-2025"],
                "points": [
                    point("Q4 2024", "24年Q4", 14.260, ["intc-10k-2025"]),
                    point("Q1 2025", "25年Q1", 12.667),
                    point("Q2 2025", "25年Q2", 12.859),
                    point("Q3 2025", "25年Q3", 13.653),
                    point("Q4 2025", "25年Q4", 13.674, ["intc-fy2025-results"]),
                    point("Q1 2026", "26年Q1", 13.577, ["intc-q1-2026"]),
                ],
            },
            {
                "id": "quarterly-gaap-gross-margin",
                "label": "Quarterly GAAP gross margin",
                "labelZh": "季度 GAAP 毛利率",
                "labelEn": "Quarterly GAAP gross margin",
                "unit": "percent",
                "cadence": "quarterly",
                "note": "Gross margin is gross profit divided by revenue.",
                "noteZh": "毛利率按毛利除以收入计算。",
                "noteEn": "Gross margin is gross profit divided by revenue.",
                "sourceIds": ["intc-sec-companyfacts", "intc-q1-2026", "intc-fy2025-results", "intc-10k-2025"],
                "points": [
                    point("Q4 2024", "24年Q4", 39.16, ["intc-10k-2025"]),
                    point("Q1 2025", "25年Q1", 36.88),
                    point("Q2 2025", "25年Q2", 27.55),
                    point("Q3 2025", "25年Q3", 38.22),
                    point("Q4 2025", "25年Q4", 36.15, ["intc-fy2025-results"]),
                    point("Q1 2026", "26年Q1", 39.38, ["intc-q1-2026"]),
                ],
            },
            {
                "id": "annual-revenue",
                "label": "Annual revenue",
                "labelZh": "年度收入",
                "labelEn": "Annual revenue",
                "unit": "USD billions",
                "cadence": "annual",
                "note": "Annual revenue in USD billions.",
                "noteZh": "年度收入，单位为十亿美元。",
                "noteEn": "Annual revenue in USD billions.",
                "sourceIds": ["intc-sec-companyfacts", "intc-10k-2025"],
                "points": [
                    point("FY2021", "21财年", 79.024),
                    point("FY2022", "22财年", 63.054),
                    point("FY2023", "23财年", 54.228),
                    point("FY2024", "24财年", 53.101),
                    point("FY2025", "25财年", 52.853, ["intc-10k-2025"]),
                ],
            },
        ],
        "revenueMixHistory": [
            period(
                "FY2023",
                "23财年",
                54.228,
                ["intc-10k-2025"],
                [
                    segment("Client Computing Group", "客户端计算事业部", 32.305, 54.228),
                    segment("Data Center and AI", "数据中心与 AI", 15.980, 54.228),
                    segment("Intel Foundry", "英特尔代工", 18.504, 54.228),
                    segment("All Other", "其他业务", 5.463, 54.228),
                ],
                "Operating segment revenue includes intersegment activity; intersegment eliminations are not shown in the stacked chart.",
                "经营分部收入包含分部间交易；堆叠图未展示分部间抵销项，不能直接加总为净收入。",
            ),
            period(
                "FY2024",
                "24财年",
                53.101,
                ["intc-10k-2025"],
                [
                    segment("Client Computing Group", "客户端计算事业部", 33.346, 53.101),
                    segment("Data Center and AI", "数据中心与 AI", 16.125, 53.101),
                    segment("Intel Foundry", "英特尔代工", 17.317, 53.101),
                    segment("All Other", "其他业务", 3.601, 53.101),
                ],
            ),
            period(
                "FY2025",
                "25财年",
                52.853,
                ["intc-10k-2025", "intc-fy2025-results"],
                [
                    segment("Client Computing Group", "客户端计算事业部", 32.228, 52.853),
                    segment("Data Center and AI", "数据中心与 AI", 16.919, 52.853),
                    segment("Intel Foundry", "英特尔代工", 17.826, 52.853),
                    segment("All Other", "其他业务", 3.563, 52.853),
                ],
            ),
        ],
    },
}


def upsert_source(sources: list[dict], source: dict) -> list[dict]:
    return [source if item.get("id") == source["id"] else item for item in sources] + (
        [] if any(item.get("id") == source["id"] for item in sources) else [source]
    )


def apply_history(company_id: str, payload: dict) -> None:
    path = COMPANIES_DIR / f"{company_id}.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    report["sources"] = upsert_source(report.get("sources", []), payload["source"])
    report.setdefault("financials", {})
    report["financials"]["trends"] = payload["trends"]
    report["financials"]["revenueMixHistory"] = payload["revenueMixHistory"]
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    for company_id, payload in FINANCIAL_HISTORY.items():
        apply_history(company_id, payload)
    print(f"Applied financial history to {len(FINANCIAL_HISTORY)} companies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
