#!/usr/bin/env python3
"""Discover cross-company event signals for tracked companies.

This scanner is intentionally conservative. It searches public news RSS
endpoints for every tracked company, classifies event candidates with simple
rules, writes review artifacts, and only updates company JSON when --apply is
explicitly passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"
ROOT_COMPANIES_DIR = ROOT / "data" / "companies"
SIGNALS_DIR = ROOT / "research" / "event-signals"

EVENT_KEYWORDS: dict[str, dict[str, Any]] = {
    "customer-competition": {
        "categoryZh": "客户/竞争格局",
        "categoryEn": "Customer / competition",
        "terms": [
            "customer becomes competitor",
            "compete with",
            "competition",
            "competitor",
            "cloud business",
            "move to the cloud",
            "excess capacity",
            "surplus capacity",
            "rent out capacity",
            "sell compute",
            "sell computing",
            "Meta Compute",
            "biggest customer to blame",
            "bad news for",
            "threat",
            "rival",
            "多余算力",
            "剩余算力",
            "竞争",
            "云业务",
        ],
        "impactZh": "这类事件可能改变客户关系、续约增长、议价能力或行业供需叙事；需要复核正式公告、管理层表述和后续订单/价格变化。",
        "impactEn": "This type of event may change customer relationships, renewal growth, bargaining power, or the industry supply-demand narrative; verify with filings, management comments, and follow-on order or pricing data.",
    },
    "contract-order": {
        "categoryZh": "订单/合同",
        "categoryEn": "Orders / contracts",
        "terms": [
            "contract",
            "agreement",
            "backlog",
            "order",
            "customer",
            "partnership",
            "deal",
            "take-or-pay",
            "合同",
            "订单",
            "客户",
            "合作",
            "中标",
        ],
        "impactZh": "这类事件可能影响收入可见度、资本开支回收和客户集中度；需要确认合同金额、期限、取消条款和交付节奏。",
        "impactEn": "This type of event may affect revenue visibility, capex payback, and customer concentration; verify contract size, duration, cancellation terms, and delivery timing.",
    },
    "capacity-supply": {
        "categoryZh": "产能/供给",
        "categoryEn": "Capacity / supply",
        "terms": [
            "capacity",
            "data center",
            "factory",
            "fab",
            "production",
            "shipment",
            "supply",
            "shortage",
            "oversupply",
            "utilization",
            "产能",
            "供给",
            "扩产",
            "投产",
            "短缺",
            "过剩",
        ],
        "impactZh": "这类事件可能影响产业链卡点、价格、交付周期和利润率；需要交叉验证产能规模、时间点和客户认证。",
        "impactEn": "This type of event may affect scarce layers, pricing, delivery lead times, and margins; cross-check capacity scale, timing, and customer qualification.",
    },
    "pricing-commodity": {
        "categoryZh": "价格/原材料",
        "categoryEn": "Pricing / commodities",
        "terms": [
            "price hike",
            "price cut",
            "pricing",
            "commodity",
            "raw material",
            "tariff",
            "涨价",
            "降价",
            "价格",
            "原材料",
            "关税",
        ],
        "impactZh": "这类事件可能影响收入弹性、成本压力或替代需求；需要跟踪价格传导、库存和毛利率。",
        "impactEn": "This type of event may affect revenue leverage, cost pressure, or substitution demand; track price pass-through, inventory, and gross margin.",
    },
    "regulatory-policy": {
        "categoryZh": "政策/监管",
        "categoryEn": "Policy / regulation",
        "terms": [
            "export control",
            "sanction",
            "regulation",
            "regulatory",
            "approval",
            "investigation",
            "ban",
            "license",
            "出口管制",
            "制裁",
            "监管",
            "审批",
            "调查",
            "禁令",
            "许可证",
        ],
        "impactZh": "这类事件可能影响可销售市场、供应链路径、客户采购和合规成本；需要优先核对监管原文。",
        "impactEn": "This type of event may affect addressable markets, supply-chain routing, customer procurement, and compliance costs; prioritize original regulatory text.",
    },
    "financing-capex": {
        "categoryZh": "融资/资本开支",
        "categoryEn": "Financing / capex",
        "terms": [
            "convertible",
            "debt",
            "offering",
            "financing",
            "capex",
            "investment",
            "raise",
            "融资",
            "债券",
            "可转债",
            "资本开支",
            "投资",
            "定增",
        ],
        "impactZh": "这类事件可能影响扩产资金、摊薄、资产负债表和现金流压力；需要确认融资条款和资金用途。",
        "impactEn": "This type of event may affect expansion funding, dilution, balance-sheet risk, and cash-flow pressure; verify financing terms and use of proceeds.",
    },
    "earnings-guidance": {
        "categoryZh": "业绩/指引",
        "categoryEn": "Earnings / guidance",
        "terms": [
            "earnings",
            "results",
            "guidance",
            "forecast",
            "outlook",
            "revenue",
            "margin",
            "profit",
            "财报",
            "业绩",
            "指引",
            "收入",
            "利润",
            "毛利率",
        ],
        "impactZh": "这类事件可能影响最新业绩口径和趋势判断；需要用公司公告或 SEC/交易所文件更新财务模块。",
        "impactEn": "This type of event may affect the latest financial baseline and trend judgment; update financial modules from company releases or SEC/exchange filings.",
    },
}

SOURCE_STRENGTH_HINTS = {
    "Reuters": "medium",
    "Bloomberg": "medium",
    "MarketWatch": "medium",
    "Barron's": "medium",
    "Investopedia": "medium",
    "Investor's Business Daily": "medium",
    "Business Insider": "medium",
    "CNBC": "medium",
    "SEC": "strong",
}

EVIDENCE_RANK = {"strong": 3, "medium": 2, "weak": 1, "needs-checking": 0}


@dataclass
class Signal:
    company_id: str
    ticker: str
    company_name: str
    title: str
    link: str
    source_name: str
    published_at: str
    summary: str
    category: str
    category_zh: str
    category_en: str
    impact_zh: str
    impact_en: str
    score: int
    matched_aliases: list[str]
    matched_terms: list[str]
    evidence_level: str

    @property
    def source_id(self) -> str:
        digest = hashlib.sha1(f"{self.link}|{self.title}".encode("utf-8")).hexdigest()[:10]
        return f"event-{self.company_id}-{digest}"


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str | None) -> str:
    if not value:
        return datetime.now(UTC).date().isoformat()
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError):
        return value[:10]


def date_in_window(value: str, cutoff: datetime) -> bool:
    try:
        parsed = datetime.fromisoformat(value[:10]).replace(tzinfo=UTC)
    except ValueError:
        return False
    return parsed >= cutoff


def compact_aliases(report: dict[str, Any]) -> list[str]:
    raw = [
        report.get("ticker", ""),
        report.get("name", ""),
        report.get("legalName", ""),
        *report.get("aliases", []),
    ]
    aliases: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        for part in re.split(r"\s*/\s*|\s+\|\s+", item):
            part = part.strip()
            if len(part) < 2:
                continue
            if part not in aliases:
                aliases.append(part)
    return aliases[:8]


def event_query(report: dict[str, Any], lookback_days: int) -> str:
    aliases = compact_aliases(report)
    preferred = [alias for alias in aliases if len(alias) <= 32][:4] or aliases[:2]
    alias_clause = " OR ".join(f'"{alias}"' if " " in alias else alias for alias in preferred)
    if report.get("market") == "CN":
        terms = "公告 OR 合同 OR 订单 OR 产能 OR 涨价 OR 政策 OR 监管 OR 客户"
    else:
        terms = (
            '"excess capacity" OR "cloud business" OR contract OR customer OR competitor OR '
            'capacity OR "export control" OR earnings OR guidance OR financing'
        )
    return f"({alias_clause}) ({terms}) when:{lookback_days}d"


def fetch_google_news(query: str, region: str, limit: int) -> list[dict[str, str]]:
    params = {
        "q": query,
        "hl": "zh-CN" if region == "CN" else "en-US",
        "gl": "CN" if region == "CN" else "US",
        "ceid": "CN:zh-Hans" if region == "CN" else "US:en",
    }
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "Stock-Checking research bot"})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()

    root = ET.fromstring(raw)
    parsed: list[dict[str, str]] = []
    for item in root.findall(".//item")[:limit]:
        source = item.find("source")
        parsed.append(
            {
                "title": clean_text(item.findtext("title")),
                "link": clean_text(item.findtext("link")),
                "summary": clean_text(item.findtext("description")),
                "publishedAt": parse_date(item.findtext("pubDate")),
                "sourceName": clean_text(source.text if source is not None else ""),
            }
        )
    return [item for item in parsed if item["title"] and item["link"]]


def match_signal(report: dict[str, Any], item: dict[str, str]) -> Signal | None:
    title = item["title"]
    summary = item.get("summary", "")
    text = f"{title} {summary}".lower()
    aliases = compact_aliases(report)
    matched_aliases = [alias for alias in aliases if alias.lower() in text]
    if not matched_aliases:
        return None

    best_key = ""
    best_terms: list[str] = []
    for key, config in EVENT_KEYWORDS.items():
        terms = [term for term in config["terms"] if term.lower() in text]
        if len(terms) > len(best_terms):
            best_key = key
            best_terms = terms
    if not best_key:
        return None

    source_name = item.get("sourceName") or "Google News"
    score = 4 + min(len(matched_aliases), 3) + min(len(best_terms), 4)
    if report.get("ticker", "").lower() in text:
        score += 2
    if source_name in SOURCE_STRENGTH_HINTS:
        score += 1
    if any(term in text for term in ("rumor", "unconfirmed", "reportedly", "据称", "传闻")):
        score -= 1
    score = max(1, min(score, 10))

    config = EVENT_KEYWORDS[best_key]
    return Signal(
        company_id=report["id"],
        ticker=report["ticker"],
        company_name=report["name"],
        title=title,
        link=item["link"],
        source_name=source_name,
        published_at=item["publishedAt"],
        summary=summary[:360],
        category=best_key,
        category_zh=config["categoryZh"],
        category_en=config["categoryEn"],
        impact_zh=config["impactZh"],
        impact_en=config["impactEn"],
        score=score,
        matched_aliases=matched_aliases,
        matched_terms=best_terms,
        evidence_level=SOURCE_STRENGTH_HINTS.get(source_name, "weak"),
    )


def signal_payload(signal: Signal) -> dict[str, Any]:
    return {
        "companyId": signal.company_id,
        "ticker": signal.ticker,
        "companyName": signal.company_name,
        "date": signal.published_at,
        "title": signal.title,
        "sourceName": signal.source_name,
        "url": signal.link,
        "category": signal.category,
        "categoryZh": signal.category_zh,
        "categoryEn": signal.category_en,
        "score": signal.score,
        "matchedAliases": signal.matched_aliases,
        "matchedTerms": signal.matched_terms,
        "summary": signal.summary,
        "impactZh": signal.impact_zh,
        "impactEn": signal.impact_en,
        "evidenceLevel": signal.evidence_level,
        "reviewNoteZh": "该条为自动发现的外部事件线索，落库前应复核原始报道、公司公告或监管文件。",
        "reviewNoteEn": "Automatically discovered external event lead. Verify original reporting, company releases, or regulatory filings before treating it as confirmed.",
    }


def upsert_event(report: dict[str, Any], signal: Signal) -> bool:
    sources = report.setdefault("sources", [])
    news = report.setdefault("news", [])
    if any(item.get("id") == signal.source_id for item in sources):
        return False
    if any(item.get("title") == signal.title for item in news):
        return False

    sources.insert(
        0,
        {
            "id": signal.source_id,
            "title": signal.title,
            "titleZh": f"外部事件线索：{signal.title}",
            "titleEn": signal.title,
            "publisher": signal.source_name,
            "url": signal.link,
            "publishedAt": signal.published_at,
            "accessedAt": datetime.now(UTC).date().isoformat(),
            "type": "news",
            "evidenceLevel": signal.evidence_level,
            "evidenceLevelZh": {"strong": "强证据", "medium": "中等证据"}.get(signal.evidence_level, "弱证据"),
            "evidenceLevelEn": signal.evidence_level.capitalize(),
        },
    )
    news.insert(
        0,
        {
            "date": signal.published_at,
            "title": signal.title,
            "titleZh": f"外部事件线索：{signal.title}",
            "titleEn": signal.title,
            "category": signal.category_en,
            "categoryZh": signal.category_zh,
            "categoryEn": signal.category_en,
            "summary": signal.summary or signal.title,
            "summaryZh": (
                f"自动发现的外部事件线索：{signal.title}。匹配词："
                f"{'、'.join(signal.matched_terms[:5])}。需要用原始报道、公司公告或监管文件复核。"
            ),
            "summaryEn": signal.summary or signal.title,
            "impact": signal.impact_zh,
            "impactZh": signal.impact_zh,
            "impactEn": signal.impact_en,
            "sourceIds": [signal.source_id],
        },
    )
    news.sort(key=lambda entry: entry.get("date", ""), reverse=True)
    report["news"] = news[:24]
    report["lastUpdated"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return True


def prune_event_signals(report: dict[str, Any], cutoff: datetime) -> bool:
    stale_source_ids = {
        source.get("id")
        for source in report.get("sources", [])
        if isinstance(source, dict)
        and str(source.get("id", "")).startswith("event-")
        and not date_in_window(str(source.get("publishedAt", "")), cutoff)
    }
    if not stale_source_ids:
        return False

    report["sources"] = [source for source in report.get("sources", []) if source.get("id") not in stale_source_ids]
    report["news"] = [
        item
        for item in report.get("news", [])
        if not any(source_id in stale_source_ids for source_id in item.get("sourceIds", []))
    ]
    report["lastUpdated"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return True


def load_reports(tickers: set[str] | None) -> list[tuple[Path, dict[str, Any]]]:
    reports: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(COMPANIES_DIR.glob("*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        if tickers and report.get("ticker", "").upper() not in tickers and report.get("id", "").upper() not in tickers:
            continue
        reports.append((path, report))
    return reports


def write_report(path: Path, report: dict[str, Any]) -> None:
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    path.write_text(content, encoding="utf-8")
    mirror = ROOT_COMPANIES_DIR / path.name
    if mirror.exists():
        mirror.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover cross-company event signals.")
    parser.add_argument("--tickers", help="Comma-separated tickers or ids to scan. Defaults to all companies.")
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=8, help="Max RSS items per company.")
    parser.add_argument("--min-score", type=int, default=8, help="Minimum score to apply to company news.")
    parser.add_argument("--apply", action="store_true", help="Write high-scoring signals into company JSON.")
    parser.add_argument("--include-weak", action="store_true", help="Allow weak evidence sources in apply mode.")
    parser.add_argument(
        "--prune-out-of-window",
        action="store_true",
        help="In apply mode, remove event-* news/sources older than the lookback window.",
    )
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between company requests.")
    args = parser.parse_args()

    tickers = {item.strip().upper() for item in args.tickers.split(",")} if args.tickers else None
    reports = load_reports(tickers)
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

    all_signals: list[Signal] = []
    failures: list[dict[str, str]] = []
    changed = 0
    cutoff = datetime.now(UTC) - timedelta(days=args.lookback_days)

    for path, report in reports:
        query = event_query(report, args.lookback_days)
        try:
            items = fetch_google_news(query, report.get("market", "US"), args.limit)
        except Exception as exc:  # noqa: BLE001
            failures.append({"ticker": report.get("ticker", path.stem), "error": str(exc), "query": query})
            continue

        signals = [
            signal
            for item in items
            if date_in_window(item.get("publishedAt", ""), cutoff) and (signal := match_signal(report, item))
        ]
        signals.sort(key=lambda signal: (signal.score, signal.published_at), reverse=True)
        all_signals.extend(signals)

        draft = {
            "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "companyId": report["id"],
            "ticker": report["ticker"],
            "query": query,
            "applied": bool(args.apply),
            "signals": [signal_payload(signal) for signal in signals],
        }
        (SIGNALS_DIR / f"{report['id']}.event-signals.json").write_text(
            json.dumps(draft, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        if args.apply:
            touched = prune_event_signals(report, cutoff) if args.prune_out_of_window else False
            for signal in signals:
                if signal.score < args.min_score:
                    continue
                if signal.evidence_level == "weak" and not args.include_weak:
                    continue
                touched = upsert_event(report, signal) or touched
            if touched:
                write_report(path, report)
                changed += 1
                print(f"Applied event signals: {report['ticker']}")

        time.sleep(args.sleep)

    summary = {
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "companyCount": len(reports),
        "signalCount": len(all_signals),
        "appliedCompanyCount": changed,
        "minScoreForApply": args.min_score,
        "apply": bool(args.apply),
        "failures": failures,
        "actionableSignals": [
            signal_payload(signal)
            for signal in sorted(
                [signal for signal in all_signals if signal.evidence_level != "weak"],
                key=lambda item: (EVIDENCE_RANK.get(item.evidence_level, 0), item.score, item.published_at),
                reverse=True,
            )[:50]
        ],
        "topSignals": [
            signal_payload(signal)
            for signal in sorted(all_signals, key=lambda item: (item.score, item.published_at), reverse=True)[:50]
        ],
    }
    (SIGNALS_DIR / "event-signals-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Event signal scan complete; companies={len(reports)} signals={len(all_signals)} "
        f"appliedCompanies={changed} failures={len(failures)}"
    )
    if failures:
        for failure in failures[:5]:
            print(f"Warning: {failure['ticker']} failed: {failure['error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
