#!/usr/bin/env python3
"""Build review drafts for adding or refreshing company research.

This script is intentionally conservative: it gathers structured evidence and
writes draft JSON files under research/drafts, but it does not modify the live
company data consumed by the GitHub Pages app.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WATCHLIST = ROOT / "config" / "research-watchlist.json"
DEFAULT_OUTPUT = ROOT / "research" / "drafts"

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
CNINFO_ANNOUNCEMENT_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
EASTMONEY_ANNOUNCEMENT_URL = "https://np-anotice-stock.eastmoney.com/api/security/ann"

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "Stock-Checking research bot contact@example.com")
REQUEST_TIMEOUT = 30

SEC_RELEVANT_FORMS = {"10-K", "10-Q", "8-K", "20-F", "40-F", "6-K"}
SEC_SINGLE_QUARTER_FRAME = re.compile(r"^CY\d{4}Q[1-4]I?$")

FINANCIAL_CONCEPTS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractsWithCustomers",
        "Revenue",
        "Revenues",
        "SalesRevenueNet",
    ],
    "net_income": ["NetIncomeLoss", "ProfitLossAttributableToOwnersOfParent", "ProfitLoss"],
    "operating_income": ["OperatingIncomeLoss", "ProfitLossFromOperatingActivities"],
    "gross_profit": ["GrossProfit"],
    "assets": ["Assets"],
    "cash_from_operations": ["NetCashProvidedByUsedInOperatingActivities", "CashFlowsFromUsedInOperatingActivities"],
    "diluted_eps": ["EarningsPerShareDiluted"],
}

FINANCIAL_TAXONOMIES = ("us-gaap", "ifrs-full")
FINANCIAL_UNITS = {"USD", "EUR", "TWD", "CNY", "USD/shares", "EUR/shares", "TWD/shares", "CNY/shares"}

CNINFO_EXCHANGE = {
    "SSE": {"column": "sse", "plate": "sh"},
    "SH": {"column": "sse", "plate": "sh"},
    "SZSE": {"column": "szse", "plate": "sz"},
    "SZ": {"column": "szse", "plate": "sz"},
    "BSE": {"column": "bj", "plate": "bj"},
    "BJ": {"column": "bj", "plate": "bj"},
}


@dataclass
class Target:
    query: str
    market: str
    enabled: bool = True
    exchange: str | None = None
    name: str | None = None
    notes: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return cleaned.strip("-").lower() or "company"


def request_text(url: str, *, headers: dict[str, str] | None = None, form: dict[str, str] | None = None) -> str:
    request_headers = {"User-Agent": "Stock-Checking research bot", "Accept": "application/json"}
    if headers:
        request_headers.update(headers)

    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        request_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    request = urllib.request.Request(url, data=data, headers=request_headers)
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        raw = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            raw = gzip.decompress(raw)
    return raw.decode("utf-8")


def request_json(url: str, *, headers: dict[str, str] | None = None, form: dict[str, str] | None = None) -> Any:
    return json.loads(request_text(url, headers=headers, form=form))


def parse_jsonp(value: str) -> Any:
    value = value.strip()
    start = value.find("(")
    end = value.rfind(")")
    if start == -1 or end == -1 or end <= start:
        return json.loads(value)
    return json.loads(value[start + 1 : end])


def sec_json(url: str) -> Any:
    return request_json(url, headers={"User-Agent": SEC_USER_AGENT})


def load_watchlist(path: Path, *, include_disabled: bool) -> list[Target]:
    data = json.loads(path.read_text(encoding="utf-8"))
    targets: list[Target] = []
    for item in data.get("targets", []):
        enabled = bool(item.get("enabled", True))
        if not enabled and not include_disabled:
            continue
        targets.append(
            Target(
                query=str(item["query"]),
                market=str(item.get("market", "auto")).upper(),
                enabled=enabled,
                exchange=item.get("exchange"),
                name=item.get("name"),
                notes=item.get("notes"),
            )
        )
    return targets


def targets_from_args(args: argparse.Namespace) -> list[Target]:
    targets: list[Target] = []
    watchlist = Path(args.watchlist) if args.watchlist else None
    if watchlist is None and not args.target:
        watchlist = DEFAULT_WATCHLIST
    if watchlist:
        targets.extend(load_watchlist(watchlist, include_disabled=args.include_disabled))
    for value in args.target or []:
        targets.append(Target(query=value, market=args.market.upper(), exchange=args.exchange))
    if not targets:
        raise SystemExit("No targets supplied. Use --target or --watchlist.")
    return targets


def load_sec_ticker_map() -> list[dict[str, Any]]:
    data = sec_json(SEC_TICKERS_URL)
    return list(data.values())


def resolve_us_target(target: Target, ticker_map: list[dict[str, Any]]) -> dict[str, Any]:
    query = target.query.strip()
    upper = query.upper()
    matches = []

    for entry in ticker_map:
        ticker = str(entry.get("ticker", "")).upper()
        title = str(entry.get("title", "")).upper()
        cik = str(entry.get("cik_str", ""))
        if upper in {ticker, cik, cik.zfill(10)} or upper in title:
            matches.append(entry)

    if not matches:
        raise ValueError(f"No SEC ticker-map match for {target.query}")

    exact = [entry for entry in matches if str(entry.get("ticker", "")).upper() == upper]
    entry = exact[0] if exact else matches[0]
    cik = str(entry["cik_str"]).zfill(10)
    return {
        "query": target.query,
        "market": "US",
        "ticker": entry.get("ticker"),
        "name": entry.get("title"),
        "cik": cik,
        "confidence": "high" if exact else "medium",
        "source": SEC_TICKERS_URL,
    }


def sec_archive_url(cik: str, accession: str, primary_doc: str) -> str:
    cik_int = str(int(cik))
    accession_no_dash = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dash}/{primary_doc}"


def extract_sec_filings(submissions: dict[str, Any], cik: str, *, limit: int = 16) -> list[dict[str, Any]]:
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    filings: list[dict[str, Any]] = []

    for index, form in enumerate(forms):
        if form not in SEC_RELEVANT_FORMS:
            continue
        accession = recent.get("accessionNumber", [""])[index]
        primary_doc = recent.get("primaryDocument", [""])[index]
        filing_date = recent.get("filingDate", [""])[index]
        report_date = recent.get("reportDate", [""])[index]
        filings.append(
            {
                "form": form,
                "filedAt": filing_date,
                "reportDate": report_date,
                "accessionNumber": accession,
                "primaryDocument": primary_doc,
                "url": sec_archive_url(cik, accession, primary_doc) if accession and primary_doc else "",
            }
        )
        if len(filings) >= limit:
            break

    return filings


def pick_financial_unit(units: dict[str, Any]) -> str | None:
    for unit in units:
        if unit in FINANCIAL_UNITS:
            return unit
    return None


def fact_sort_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("filed", "")), str(item.get("end", "")))


def latest_series_fact_key(facts: list[dict[str, Any]]) -> tuple[str, str]:
    candidates = [
        fact
        for fact in facts
        if fact.get("form") in SEC_RELEVANT_FORMS and isinstance(fact.get("val"), (int, float))
    ]
    if not candidates:
        return ("", "")
    return max(fact_sort_key(fact) for fact in candidates)


def pick_fact_series(companyfacts: dict[str, Any], concept_names: list[str]) -> dict[str, Any] | None:
    facts_by_taxonomy = companyfacts.get("facts", {})
    candidates: list[dict[str, Any]] = []
    for taxonomy_index, taxonomy in enumerate(FINANCIAL_TAXONOMIES):
        concepts = facts_by_taxonomy.get(taxonomy, {})
        for concept_index, concept in enumerate(concept_names):
            concept_data = concepts.get(concept)
            if not concept_data:
                continue
            units = concept_data.get("units", {})
            unit = pick_financial_unit(units)
            if not unit:
                continue
            facts = units[unit]
            latest_key = latest_series_fact_key(facts)
            if latest_key == ("", ""):
                continue
            candidates.append(
                {
                    "sortKey": (*latest_key, -taxonomy_index, -concept_index),
                    "taxonomy": taxonomy,
                    "concept": concept,
                    "label": concept_data.get("label") or concept,
                    "unit": unit,
                    "facts": facts,
                }
            )
    if candidates:
        best = max(candidates, key=lambda item: item["sortKey"])
        return {
            "taxonomy": best["taxonomy"],
            "concept": best["concept"],
            "label": best["label"],
            "unit": best["unit"],
            "facts": best["facts"],
        }
    return None


def normalized_fact(item: dict[str, Any], unit: str) -> dict[str, Any]:
    return {
        "end": item.get("end"),
        "fy": item.get("fy"),
        "fp": item.get("fp"),
        "form": item.get("form"),
        "filed": item.get("filed"),
        "frame": item.get("frame"),
        "value": item.get("val"),
        "unit": unit,
        "accession": item.get("accn"),
    }


def is_single_quarter_fact(fact: dict[str, Any]) -> bool:
    frame = fact.get("frame")
    return isinstance(frame, str) and bool(SEC_SINGLE_QUARTER_FRAME.match(frame))


def latest_facts(
    facts: list[dict[str, Any]],
    unit: str,
    *,
    forms: set[str],
    limit: int,
    fact_filter: Any | None = None,
) -> list[dict[str, Any]]:
    candidates = [
        fact
        for fact in facts
        if fact.get("form") in forms
        and isinstance(fact.get("val"), (int, float))
        and (fact_filter is None or fact_filter(fact))
    ]
    candidates.sort(key=lambda item: (str(item.get("filed", "")), str(item.get("end", ""))), reverse=True)

    seen: set[tuple[Any, Any, Any]] = set()
    picked: list[dict[str, Any]] = []
    for item in candidates:
        key = (item.get("end"), item.get("fp"), item.get("form"))
        if key in seen:
            continue
        seen.add(key)
        picked.append(normalized_fact(item, unit))
        if len(picked) >= limit:
            break
    return picked


def extract_sec_financials(companyfacts: dict[str, Any]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for metric, concepts in FINANCIAL_CONCEPTS.items():
        series = pick_fact_series(companyfacts, concepts)
        if not series:
            metrics[metric] = {"status": "missing", "conceptCandidates": concepts}
            continue
        facts = series["facts"]
        unit = series["unit"]
        metrics[metric] = {
            "status": "ok",
            "taxonomy": series["taxonomy"],
            "concept": series["concept"],
            "label": series["label"],
            "unit": unit,
            "annual": latest_facts(facts, unit, forms={"10-K", "20-F", "40-F"}, limit=5),
            "quarterly": latest_facts(facts, unit, forms={"10-Q"}, limit=8, fact_filter=is_single_quarter_fact),
        }
    return metrics


def build_us_draft(target: Target, ticker_map: list[dict[str, Any]]) -> dict[str, Any]:
    identity = resolve_us_target(target, ticker_map)
    cik = identity["cik"]
    submissions = sec_json(SEC_SUBMISSIONS_URL.format(cik=cik))
    companyfacts = sec_json(SEC_COMPANYFACTS_URL.format(cik=cik))

    filings = extract_sec_filings(submissions, cik)
    financials = extract_sec_financials(companyfacts)
    exchanges = submissions.get("exchanges", [])
    tickers = submissions.get("tickers", [])

    return {
        "schemaVersion": 1,
        "draftType": "company-research",
        "generatedAt": utc_now(),
        "target": target.__dict__,
        "identity": {
            **identity,
            "legalName": submissions.get("name"),
            "sic": submissions.get("sic"),
            "sicDescription": submissions.get("sicDescription"),
            "exchanges": exchanges,
            "tickers": tickers,
            "fiscalYearEnd": submissions.get("fiscalYearEnd"),
        },
        "filings": filings,
        "financials": financials,
        "sources": [
            {
                "id": "sec-company-tickers",
                "publisher": "SEC EDGAR",
                "url": SEC_TICKERS_URL,
                "type": "sec",
                "accessedAt": today(),
            },
            {
                "id": "sec-submissions",
                "publisher": "SEC EDGAR",
                "url": SEC_SUBMISSIONS_URL.format(cik=cik),
                "type": "sec",
                "accessedAt": today(),
            },
            {
                "id": "sec-companyfacts",
                "publisher": "SEC EDGAR",
                "url": SEC_COMPANYFACTS_URL.format(cik=cik),
                "type": "sec",
                "accessedAt": today(),
            },
        ],
        "coverage": {
            "automated": [
                "ticker/CIK resolution",
                "recent SEC filings",
                "standard XBRL financial concepts",
            ],
            "manualReviewRequired": [
                "business segment narrative",
                "revenue mix labels and company-specific segment mapping",
                "supplier/customer relationships",
                "raw-material upstream tracing",
                "Chinese translation and final investment thesis",
            ],
        },
    }


def infer_cn_exchange(target: Target) -> str:
    if target.exchange:
        return target.exchange.upper()
    query = target.query.strip()
    if query.startswith(("6", "9")):
        return "SSE"
    if query.startswith(("0", "2", "3")):
        return "SZSE"
    if query.startswith(("4", "8")):
        return "BSE"
    return "SSE"


def cninfo_announcement_url(item: dict[str, Any]) -> str:
    adjunct = item.get("adjunctUrl")
    if adjunct:
        return urllib.parse.urljoin("https://static.cninfo.com.cn/", adjunct)
    announcement_id = item.get("announcementId", "")
    sec_code = item.get("secCode", "")
    org_id = item.get("orgId", "")
    announcement_time = item.get("announcementTime", "")
    return (
        "https://www.cninfo.com.cn/new/disclosure/detail?"
        + urllib.parse.urlencode(
            {
                "stockCode": sec_code,
                "announcementId": announcement_id,
                "orgId": org_id,
                "announcementTime": announcement_time,
            }
        )
    )


def classify_cn_announcement(title: str) -> str:
    title = re.sub(r"<[^>]+>", "", title)
    if "年度报告" in title and "摘要" not in title:
        return "annual_report"
    if "第一季度报告" in title:
        return "q1_report"
    if "半年度报告" in title and "摘要" not in title:
        return "half_year_report"
    if "第三季度报告" in title:
        return "q3_report"
    if "权益分派" in title or "利润分配" in title:
        return "dividend"
    if "异常波动" in title or "风险提示" in title:
        return "risk"
    if "投资者关系" in title or "调研" in title:
        return "investor_relations"
    return "other"


def clean_cn_title(title: str) -> str:
    title = re.sub(r"<[^>]+>", "", title)
    return re.sub(r"\s+", " ", title).strip()


def fetch_cninfo_announcements(target: Target, *, page_size: int = 30) -> list[dict[str, Any]]:
    exchange = infer_cn_exchange(target)
    market = CNINFO_EXCHANGE.get(exchange, CNINFO_EXCHANGE["SSE"])
    form = {
        "stock": target.query,
        "searchkey": "",
        "plate": market["plate"],
        "category": "",
        "trade": "",
        "column": market["column"],
        "columnTitle": "历史公告查询",
        "pageNum": "1",
        "pageSize": str(page_size),
        "tabName": "fulltext",
        "sortName": "",
        "sortType": "",
        "limit": "",
        "showTitle": "",
        "seDate": "",
    }
    headers = {
        "Referer": "https://www.cninfo.com.cn/new/disclosure/stock",
        "X-Requested-With": "XMLHttpRequest",
    }
    data = request_json(CNINFO_ANNOUNCEMENT_URL, headers=headers, form=form)
    items = []
    if isinstance(data, dict):
        items = data.get("announcements") or []

    announcements = []
    for item in items:
        title = clean_cn_title(str(item.get("announcementTitle", "")))
        if not title:
            continue
        announcements.append(
            {
                "title": title,
                "category": classify_cn_announcement(title),
                "publishedAt": str(item.get("announcementTime", ""))[:10],
                "secCode": item.get("secCode"),
                "secName": item.get("secName"),
                "orgId": item.get("orgId"),
                "announcementId": item.get("announcementId"),
                "url": cninfo_announcement_url(item),
                "source": "CNINFO",
            }
        )
    return announcements


def fetch_eastmoney_announcements(target: Target, *, page_size: int = 30) -> list[dict[str, Any]]:
    params = {
        "cb": f"jQuery{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "sr": "-1",
        "page_size": str(page_size),
        "page_index": "1",
        "ann_type": "A",
        "client_source": "web",
        "stock_list": target.query.strip(),
    }
    url = f"{EASTMONEY_ANNOUNCEMENT_URL}?{urllib.parse.urlencode(params)}"
    text = request_text(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Stock-Checking research bot",
            "Referer": f"https://data.eastmoney.com/notices/stock/{target.query.strip()}.html",
            "Accept": "*/*",
        },
    )
    data = parse_jsonp(text)
    items = data.get("data", {}).get("list", []) if isinstance(data, dict) else []

    announcements = []
    for item in items:
        title = clean_cn_title(str(item.get("title_ch") or item.get("title") or ""))
        if not title:
            continue
        codes = item.get("codes") or [{}]
        code_info = codes[0] if codes else {}
        stock_code = code_info.get("stock_code") or target.query.strip()
        art_code = item.get("art_code", "")
        columns = item.get("columns") or []
        column_names = [column.get("column_name") for column in columns if column.get("column_name")]
        announcements.append(
            {
                "title": title,
                "category": classify_cn_announcement(title),
                "publishedAt": str(item.get("notice_date", ""))[:10],
                "secCode": stock_code,
                "secName": code_info.get("short_name") or target.name,
                "announcementId": art_code,
                "columns": column_names,
                "url": f"https://data.eastmoney.com/notices/detail/{stock_code}/{art_code}.html" if art_code else "",
                "source": "Eastmoney announcement index",
            }
        )
    return announcements


def build_cn_draft(target: Target) -> dict[str, Any]:
    exchange = infer_cn_exchange(target)
    announcements = fetch_cninfo_announcements(target)
    announcement_source = "CNINFO"
    if not announcements:
        announcements = fetch_eastmoney_announcements(target)
        announcement_source = "Eastmoney announcement index"
    important = [item for item in announcements if item["category"] != "other"]

    return {
        "schemaVersion": 1,
        "draftType": "company-research",
        "generatedAt": utc_now(),
        "target": {**target.__dict__, "exchange": exchange},
        "identity": {
            "query": target.query,
            "market": "CN",
            "exchange": exchange,
            "name": target.name,
            "confidence": "medium",
            "source": announcement_source,
        },
        "announcements": announcements,
        "importantAnnouncements": important[:16],
        "sources": [
            {
                "id": "cninfo-announcements",
                "publisher": "CNINFO",
                "url": "https://www.cninfo.com.cn/new/index",
                "type": "exchange",
                "accessedAt": today(),
            },
            {
                "id": "eastmoney-announcement-index",
                "publisher": "Eastmoney",
                "url": "https://data.eastmoney.com/notices/",
                "type": "news",
                "accessedAt": today(),
            }
        ],
        "coverage": {
            "automated": [
                "recent announcement discovery",
                "annual/quarterly/risk/dividend/IR announcement classification",
                "direct PDF/detail links when exposed by CNINFO",
            ],
            "manualReviewRequired": [
                "PDF table extraction for financial history",
                "supplier/customer table extraction",
                "listed-company mapping for counterparties",
                "raw-material upstream tracing",
                "English translation and final investment thesis",
            ],
        },
    }


def build_draft(target: Target, ticker_map: list[dict[str, Any]] | None) -> dict[str, Any]:
    market = target.market.upper()
    if market == "AUTO":
        market = "US" if re.search(r"[A-Za-z]", target.query) else "CN"

    if market == "US":
        if ticker_map is None:
            ticker_map = load_sec_ticker_map()
        return build_us_draft(target, ticker_map)
    if market == "CN":
        return build_cn_draft(target)
    raise ValueError(f"Unsupported market for {target.query}: {target.market}")


def write_draft(draft: dict[str, Any], output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    identity = draft.get("identity", {})
    market = str(identity.get("market", draft.get("target", {}).get("market", "unknown"))).lower()
    ticker = str(identity.get("ticker") or identity.get("query") or draft.get("target", {}).get("query", "company"))
    path = output / f"{market}-{slug(ticker)}.draft.json"
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate company research drafts from public data sources.")
    parser.add_argument("--watchlist", help="Path to research watchlist JSON. Defaults to config/research-watchlist.json when no --target is supplied.")
    parser.add_argument("--target", action="append", help="Ticker/code/name to research. May be repeated.")
    parser.add_argument("--market", default="auto", choices=["auto", "US", "CN", "us", "cn"], help="Market for --target.")
    parser.add_argument("--exchange", help="Exchange hint for CN targets, e.g. SSE, SZSE, BSE.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Directory for draft JSON files.")
    parser.add_argument("--include-disabled", action="store_true", help="Include disabled watchlist targets.")
    parser.add_argument("--plan-only", action="store_true", help="Print selected targets without network calls.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = targets_from_args(args)

    if args.plan_only:
        print(json.dumps([target.__dict__ for target in targets], ensure_ascii=False, indent=2))
        return 0

    output = Path(args.output)
    ticker_map: list[dict[str, Any]] | None = None
    written: list[Path] = []
    failures: list[dict[str, str]] = []

    for target in targets:
        try:
            if target.market.upper() in {"US", "AUTO"} and re.search(r"[A-Za-z]", target.query):
                ticker_map = ticker_map or load_sec_ticker_map()
            draft = build_draft(target, ticker_map)
            path = write_draft(draft, output)
            written.append(path)
            print(f"Wrote {display_path(path)}")
        except Exception as exc:  # noqa: BLE001
            failures.append({"target": target.query, "error": str(exc)})
            print(f"Warning: failed to draft {target.query}: {exc}", file=sys.stderr)

    if failures:
        failure_path = output / "research-failures.json"
        output.mkdir(parents=True, exist_ok=True)
        failure_path.write_text(json.dumps(failures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {display_path(failure_path)}")

    print(f"Research draft pipeline complete; written={len(written)} failures={len(failures)}")
    return 1 if failures and not written else 0


if __name__ == "__main__":
    sys.exit(main())
