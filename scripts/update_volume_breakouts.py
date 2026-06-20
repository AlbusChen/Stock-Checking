#!/usr/bin/env python3
"""Refresh daily A-share volume breakout candidates for the static app."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import math
import re
import statistics
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.8 fallback for local machines.
    ZoneInfo = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "public" / "data" / "volume-breakouts.json"
EASTMONEY_QUOTE_API = "https://push2delay.eastmoney.com/api/qt/clist/get"
EASTMONEY_KLINE_API = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
EASTMONEY_ANN_API = "https://np-anotice-stock.eastmoney.com/api/security/ann"
EASTMONEY_SEARCH_API = "https://search-api-web.eastmoney.com/search/jsonp"
YAHOO_CHART_API = "https://query1.finance.yahoo.com/v8/finance/chart"
EASTMONEY_QUOTE_BASE = "https://quote.eastmoney.com"
THS_WENCAI_URL = "https://www.iwencai.com"
A_SHARE_FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
WINDOWS = (1, 2, 3, 20, 60, 120)
PAGE_SIZE = 100
MIN_AMOUNT_CNY = 50_000_000
MIN_TURNOVER_RATE = 1.0
MIN_VOLUME_RATIO = 1.8
MIN_SPOT_VOLUME_RATIO = 1.5
MIN_PCT_CHANGE = 0.0
MIN_BREAKOUT_PCT = 0.0
REQUEST_TIMEOUT = 16
THS_QUERY_TIMEOUT = 35
CATALYST_LOOKBACK_DAYS = 30
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Stock-Checking/1.0 Safari/537.36"
)

CandidateProvider = str


CATALYST_RULES = [
    {
        "typeZh": "订单/中标/客户",
        "typeEn": "Orders / tenders / customers",
        "keywords": ("中标", "订单", "合同", "大客户", "客户", "供应", "采购", "框架协议", "项目合作"),
        "score": 5,
    },
    {
        "typeZh": "产品涨价/供需紧张",
        "typeEn": "Price hikes / tight supply",
        "keywords": ("涨价", "提价", "价格上调", "供需", "短缺", "稀缺", "缺货", "供应紧张", "产能紧张"),
        "score": 5,
    },
    {
        "typeZh": "业绩改善",
        "typeEn": "Earnings improvement",
        "keywords": ("业绩预告", "业绩快报", "净利润", "利润增长", "扭亏", "同比增长", "营收增长", "分红"),
        "score": 4,
    },
    {
        "typeZh": "并购/重组/融资",
        "typeEn": "M&A / restructuring / financing",
        "keywords": ("并购", "收购", "重组", "资产注入", "定增", "发行股份", "重大资产", "控制权"),
        "score": 4,
    },
    {
        "typeZh": "政策/产业主题",
        "typeEn": "Policy / sector theme",
        "keywords": ("政策", "国常会", "工信部", "发改委", "补贴", "国产替代", "创新药", "半导体", "人工智能", "机器人", "低空经济", "算力", "概念", "板块"),
        "score": 3,
    },
    {
        "typeZh": "产能/产品进展",
        "typeEn": "Capacity / product progress",
        "keywords": ("产能", "投产", "扩产", "试生产", "量产", "认证", "新产品", "研发", "临床", "获批"),
        "score": 3,
    },
    {
        "typeZh": "资本动作",
        "typeEn": "Capital action",
        "keywords": ("回购", "增持", "员工持股", "股权激励", "战略投资"),
        "score": 3,
    },
    {
        "typeZh": "监管/风险事件",
        "typeEn": "Regulatory / risk event",
        "keywords": ("问询函", "监管", "立案", "处罚", "风险提示", "异动公告", "澄清"),
        "score": 2,
    },
    {
        "typeZh": "交易性报道",
        "typeEn": "Trading-flow report",
        "keywords": ("龙虎榜", "成交额", "换手率", "涨停", "主力资金", "融资融券", "大宗交易", "异动"),
        "score": 1,
    },
]


def market_now() -> dt.datetime:
    if ZoneInfo is None:
        return dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    return dt.datetime.now(ZoneInfo("Asia/Shanghai"))


def request_json(url: str, params: dict[str, Any], attempts: int = 3) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(params, safe=":+,")
    full_url = f"{url}?{encoded}"
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                full_url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json,text/plain,*/*",
                    "Referer": EASTMONEY_QUOTE_BASE,
                },
            )
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - retry any transient network/API error.
            last_error = exc
            if attempt < attempts:
                time.sleep(0.7 * attempt)

    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def request_jsonp(url: str, params: dict[str, Any], attempts: int = 3) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(params)
    full_url = f"{url}?{encoded}"
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                full_url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json,text/plain,*/*",
                    "Referer": "https://so.eastmoney.com/",
                },
            )
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                text = response.read().decode("utf-8").strip()
            if text.startswith("(") and text.endswith(")"):
                text = text[1:-1]
            if text.endswith(";"):
                text = text[:-1]
            if text.startswith("(") and text.endswith(")"):
                text = text[1:-1]
            return json.loads(text)
        except Exception as exc:  # noqa: BLE001 - retry any transient network/API error.
            last_error = exc
            if attempt < attempts:
                time.sleep(0.7 * attempt)

    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(value: Any) -> dt.datetime | None:
    if value in (None, "", "-"):
        return None
    text = str(value)
    cleaned = re.sub(r"(\d{2}:\d{2}:\d{2}):(\d+)", r"\1.\2", text)
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = dt.datetime.strptime(cleaned[:26], fmt)
            return parsed.replace(tzinfo=market_now().tzinfo)
        except ValueError:
            continue
    match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if match:
        try:
            parsed = dt.datetime.strptime(match.group(1), "%Y-%m-%d")
            return parsed.replace(tzinfo=market_now().tzinfo)
        except ValueError:
            return None
    return None


def in_catalyst_window(record_date: str, trade_date: str) -> bool:
    record_dt = parse_date(record_date)
    trade_dt = parse_date(trade_date)
    if not record_dt or not trade_dt:
        return True
    start = trade_dt - dt.timedelta(days=CATALYST_LOOKBACK_DAYS)
    end = trade_dt + dt.timedelta(days=2)
    return start <= record_dt <= end


def as_float(value: Any) -> float | None:
    if value in (None, "-", ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    number = as_float(value)
    if number is None:
        return None
    return int(number)


def exchange_for_code(code: str) -> str:
    if code.startswith("6"):
        return "SSE"
    if code.startswith(("4", "8", "9")):
        return "BSE"
    if code.startswith(("0", "3")):
        return "SZSE"
    return "UNKNOWN"


def secid_for_code(code: str) -> str:
    return f"1.{code}" if exchange_for_code(code) == "SSE" else f"0.{code}"


def quote_url_for_code(code: str) -> str:
    exchange = exchange_for_code(code)
    if exchange == "SSE":
        return f"{EASTMONEY_QUOTE_BASE}/sh{code}.html"
    if exchange == "BSE":
        return f"{EASTMONEY_QUOTE_BASE}/bj{code}.html"
    if exchange == "SZSE":
        return f"{EASTMONEY_QUOTE_BASE}/sz{code}.html"
    return f"{EASTMONEY_QUOTE_BASE}/{code}.html"


def announcement_url_for_code(code: str, art_code: str) -> str:
    return f"https://data.eastmoney.com/notices/detail/{code}/{art_code}.html"


def yahoo_symbol_for_code(code: str) -> str:
    exchange = exchange_for_code(code)
    if exchange == "SSE":
        return f"{code}.SS"
    if exchange == "SZSE":
        return f"{code}.SZ"
    return code


def normalize_stock_code(value: Any) -> str | None:
    match = re.search(r"(\d{6})", str(value or ""))
    return match.group(1) if match else None


def classify_catalyst(text: str) -> dict[str, Any]:
    trading_keywords = tuple(rule["keywords"] for rule in CATALYST_RULES if rule["typeZh"] == "交易性报道")[0]
    sector_keywords = tuple(rule["keywords"] for rule in CATALYST_RULES if rule["typeZh"] == "政策/产业主题")[0]
    strong_keywords = tuple(
        keyword
        for rule in CATALYST_RULES
        if rule["typeZh"] not in ("交易性报道", "政策/产业主题")
        for keyword in rule["keywords"]
    )
    if any(keyword in text for keyword in trading_keywords) and not any(keyword in text for keyword in strong_keywords + sector_keywords):
        return {
            "typeZh": "交易性报道",
            "typeEn": "Trading-flow report",
            "score": 1,
            "keywords": [keyword for keyword in trading_keywords if keyword in text][:5],
        }

    matched: list[dict[str, Any]] = []
    for rule in CATALYST_RULES:
        hits = [keyword for keyword in rule["keywords"] if keyword in text]
        if hits:
            score = int(rule["score"])
            if rule["typeZh"] != "交易性报道":
                score += min(len(hits), 3)
            matched.append(
                {
                    "typeZh": rule["typeZh"],
                    "typeEn": rule["typeEn"],
                    "score": score,
                    "keywords": hits[:5],
                }
            )

    if not matched:
        return {
            "typeZh": "未识别催化",
            "typeEn": "Unclassified catalyst",
            "score": 0,
            "keywords": [],
        }

    matched.sort(key=lambda item: item["score"], reverse=True)
    return matched[0]


def confidence_for_catalyst(source_type: str, score: int) -> tuple[str, str, str]:
    if score <= 1:
        return "context", "背景", "Context"
    if source_type == "announcement" and score >= 4:
        return "high", "高", "High"
    if score >= 4:
        return "medium", "中", "Medium"
    if score >= 2:
        return "low", "低", "Low"
    return "context", "背景", "Context"


def fetch_announcements(code: str, limit: int = 8) -> list[dict[str, Any]]:
    payload = request_json(
        EASTMONEY_ANN_API,
        {
            "sr": "-1",
            "page_size": str(limit),
            "page_index": "1",
            "ann_type": "A",
            "client_source": "web",
            "stock_list": code,
        },
    )
    items = ((payload.get("data") or {}).get("list") or [])[:limit]
    records = []
    for item in items:
        art_code = str(item.get("art_code") or "")
        title = clean_text(item.get("title"))
        date = clean_text(item.get("notice_date") or item.get("display_time") or item.get("sort_date"))
        columns = " / ".join(clean_text(column.get("column_name")) for column in item.get("columns") or [])
        records.append(
            {
                "sourceType": "announcement",
                "sourceNameZh": "东方财富公告",
                "sourceNameEn": "Eastmoney announcement",
                "title": title,
                "content": columns,
                "date": date[:10] if date else "",
                "url": announcement_url_for_code(code, art_code) if art_code else quote_url_for_code(code),
            }
        )
    return records


def fetch_news(name: str, limit: int = 8) -> list[dict[str, Any]]:
    search_param = {
        "uid": "",
        "keyword": name,
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientType": "web",
        "clientVersion": "curr",
        "param": {
            "cmsArticleWebOld": {
                "searchScope": "default",
                "sort": "default",
                "pageIndex": 1,
                "pageSize": limit,
                "preTag": "<em>",
                "postTag": "</em>",
            }
        },
    }
    payload = request_jsonp(
        EASTMONEY_SEARCH_API,
        {
            "cb": "",
            "param": json.dumps(search_param, ensure_ascii=False),
        },
    )
    items = (((payload.get("result") or {}).get("cmsArticleWebOld")) or [])[:limit]
    records = []
    for item in items:
        records.append(
            {
                "sourceType": "news",
                "sourceNameZh": clean_text(item.get("mediaName") or "东方财富资讯"),
                "sourceNameEn": "Eastmoney news",
                "title": clean_text(item.get("title")),
                "content": clean_text(item.get("content")),
                "date": clean_text(item.get("date")),
                "url": clean_text(item.get("url")),
            }
        )
    return records


def industry_watch(industry: str) -> tuple[str, str]:
    if any(token in industry for token in ("电池", "工业金属", "铜", "锂", "化学原料", "化学制品")):
        return (
            "产业核验方向：该行业对原材料价格、库存周期、下游订单和供给扰动敏感，需重点核验是否存在涨价、短缺或大客户采购消息。",
            "Industry check: this sector is sensitive to raw-material prices, inventory cycles, downstream orders and supply disruptions; verify price hikes, shortages or large-customer procurement.",
        )
    if any(token in industry for token in ("半导体", "电子化学", "计算机设备")):
        return (
            "产业核验方向：该行业更适合核验国产替代、客户认证、设备/材料订单、AI 算力或先进制程扩产等基本面线索。",
            "Industry check: verify import substitution, customer qualification, equipment/material orders, AI-compute demand or advanced-node capacity expansion.",
        )
    if any(token in industry for token in ("医疗", "制药", "生物", "CRO")):
        return (
            "产业核验方向：该行业应重点核验临床/注册进展、创新药政策、订单恢复、海外授权或投融资事件。",
            "Industry check: verify clinical or registration progress, innovative-drug policy, order recovery, out-licensing or financing events.",
        )
    if any(token in industry for token in ("通用设备", "专用设备", "航空", "机器人")):
        return (
            "产业核验方向：该行业应重点核验设备订单、政策补贴、产能利用率和下游资本开支改善。",
            "Industry check: verify equipment orders, policy support, utilization rates and downstream capex recovery.",
        )
    return (
        "产业核验方向：需要继续核验是否存在公告、订单、涨价、政策或板块景气变化，当前行业字段本身不足以证明基本面利好。",
        "Industry check: continue verifying announcements, orders, price hikes, policy support or sector-cycle changes; the industry tag alone is not proof of a catalyst.",
    )


def build_catalyst_bundle(
    row: dict[str, Any],
    latest_date: str,
    ths_candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    code = str(row.get("f12") or "")
    name = str(row.get("f14") or "")
    industry = str(row.get("f100") or "未分类")
    records: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        records.extend(fetch_announcements(code))
    except Exception as exc:  # noqa: BLE001 - optional evidence source.
        errors.append(f"announcements: {exc}")
    try:
        records.extend(fetch_news(name))
    except Exception as exc:  # noqa: BLE001 - optional evidence source.
        errors.append(f"news: {exc}")

    enriched: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        title = clean_text(record.get("title"))
        content = clean_text(record.get("content"))
        date = clean_text(record.get("date"))
        if not title or not in_catalyst_window(date, latest_date):
            continue
        key = (date[:10], title)
        if key in seen:
            continue
        seen.add(key)
        classification = classify_catalyst(f"{title} {content}")
        confidence, confidence_zh, confidence_en = confidence_for_catalyst(
            str(record.get("sourceType") or ""),
            int(classification["score"]),
        )
        enriched.append(
            {
                "sourceType": record.get("sourceType"),
                "sourceNameZh": record.get("sourceNameZh"),
                "sourceNameEn": record.get("sourceNameEn"),
                "title": title,
                "date": date[:16],
                "url": record.get("url"),
                "catalystTypeZh": classification["typeZh"],
                "catalystTypeEn": classification["typeEn"],
                "confidence": confidence,
                "confidenceZh": confidence_zh,
                "confidenceEn": confidence_en,
                "keywords": classification["keywords"],
                "summaryZh": content[:120] if content else title,
                "summaryEn": (
                    "Public source title/content indicates this catalyst category; read the linked source for full context."
                ),
                "score": int(classification["score"]),
            }
        )

    enriched.sort(key=lambda item: (int(item["score"]), str(item.get("date") or "")), reverse=True)
    fundamental = [
        item
        for item in enriched
        if int(item["score"]) >= 2 and item.get("catalystTypeZh") != "交易性报道"
    ]
    market_flow = [
        item
        for item in enriched
        if int(item["score"]) == 1 or item.get("catalystTypeZh") == "交易性报道"
    ]
    selected = (fundamental[:4] if fundamental else market_flow[:2])
    watch_zh, watch_en = industry_watch(industry)

    if fundamental:
        primary = fundamental[0]
        summary_zh = (
            f"已找到公开基本面/消息线索：{primary['date']} {primary['sourceNameZh']}《{primary['title']}》，"
            f"归类为“{primary['catalystTypeZh']}”。这只能说明存在可核验催化线索，不能单独证明上涨原因。"
        )
        summary_en = (
            f"Verified public catalyst lead found: {primary['date']} {primary['sourceNameEn']} \"{primary['title']}\", "
            f"classified as {primary['catalystTypeEn']}. It is evidence to verify, not proof of causality."
        )
        status = "found"
    elif market_flow:
        summary_zh = (
            "未找到强基本面公告或消息催化；公开资讯主要是涨停、龙虎榜、成交额等交易性报道。"
            f"{watch_zh}"
        )
        summary_en = (
            "No strong company-fundamental announcement/news catalyst was found; public items are mostly trading-flow reports. "
            f"{watch_en}"
        )
        status = "market-only"
    else:
        summary_zh = f"未在近 {CATALYST_LOOKBACK_DAYS} 天公开公告/新闻标题中找到可核验的基本面催化。{watch_zh}"
        summary_en = (
            f"No verifiable fundamental catalyst was found in public announcement/news titles within {CATALYST_LOOKBACK_DAYS} days. "
            f"{watch_en}"
        )
        status = "not-found"

    ths_signals = list(dict.fromkeys(str(item) for item in (ths_candidate or {}).get("signals", []) if item))[:6]
    if ths_signals:
        summary_zh += f" 问财公开标签可作辅助线索：{' / '.join(ths_signals[:3])}。"
        summary_en += f" iWencai public tags can be used as auxiliary clues: {' / '.join(ths_signals[:3])}."

    return {
        "status": status,
        "summaryZh": summary_zh,
        "summaryEn": summary_en,
        "industryWatchZh": watch_zh,
        "industryWatchEn": watch_en,
        "catalysts": selected,
        "errors": errors[:3],
    }


def split_signal_text(value: Any) -> list[str]:
    if value in (None, "", "-"):
        return []
    parts = re.split(r"\|\||[，,、/；;]\s*", str(value))
    return [part.strip() for part in parts if part and part.strip() and part.strip() != "-"]


def query_ths_wencai_records(query: str) -> list[dict[str, Any]]:
    code = """
import json
import sys
import warnings

warnings.filterwarnings("ignore")

import pywencai

frame = pywencai.get(query=sys.argv[1], query_type="stock", loop=False)
records = [] if frame is None else frame.to_dict("records")
print(json.dumps(records, ensure_ascii=False))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code, query],
        capture_output=True,
        check=False,
        text=True,
        timeout=THS_QUERY_TIMEOUT,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "unknown pywencai failure")[-800:])
    stdout = completed.stdout.strip()
    if not stdout:
        return []
    return json.loads(stdout)


def ths_query_for_window(days: int) -> str:
    if days == 1:
        return "今日放量突破"
    return f"今日{days}日放量突破"


def fetch_ths_wencai_candidates(windows: tuple[int, ...]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    status = {
        "id": "ths-wencai",
        "nameZh": "同花顺问财候选",
        "nameEn": "Tonghuashun iWencai candidates",
        "status": "skipped",
        "count": 0,
        "noteZh": "未启用同花顺问财候选源。",
        "noteEn": "Tonghuashun iWencai candidate source was not enabled.",
        "queries": [],
    }

    candidates: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    queries = [ths_query_for_window(days) for days in windows]

    for days, query in zip(windows, queries):
        try:
            records = query_ths_wencai_records(query)
        except Exception as exc:  # noqa: BLE001 - optional provider.
            errors.append(f"{query}: {exc}")
            continue

        for record in records:
            code = normalize_stock_code(record.get("code") or record.get("股票代码"))
            if not code:
                continue
            candidate = candidates.setdefault(
                code,
                {
                    "code": code,
                    "name": str(record.get("股票简称") or ""),
                    "sourceZh": "同花顺问财",
                    "sourceEn": "Tonghuashun iWencai",
                    "queries": [],
                    "windowDays": [],
                    "signals": [],
                    "rawLabels": [],
                },
            )
            if query not in candidate["queries"]:
                candidate["queries"].append(query)
            if days not in candidate["windowDays"]:
                candidate["windowDays"].append(days)

            for key, value in record.items():
                key_text = str(key)
                if any(token in key_text for token in ("放量突破", "技术形态", "买入信号")):
                    for signal in split_signal_text(value):
                        if signal not in candidate["signals"]:
                            candidate["signals"].append(signal)
                    if value not in (None, "", "-"):
                        raw_label = f"{key_text}: {value}"
                        if raw_label not in candidate["rawLabels"]:
                            candidate["rawLabels"].append(raw_label)

    if candidates:
        status.update(
            {
                "status": "ok" if not errors else "partial",
                "count": len(candidates),
                "noteZh": (
                    f"问财返回 {len(candidates)} 只候选；本项目随后用公开行情重新校验窗口突破和放量。"
                    if not errors
                    else f"问财返回 {len(candidates)} 只候选，部分查询失败；本项目随后用公开行情重新校验。"
                ),
                "noteEn": (
                    f"iWencai returned {len(candidates)} candidates; this project then re-validates breakout and volume with public market data."
                    if not errors
                    else f"iWencai returned {len(candidates)} candidates with partial query failures; this project then re-validates them."
                ),
                "queries": queries,
            }
        )
    else:
        status.update(
            {
                "status": "failed",
                "noteZh": "问财未返回可用候选，已回退到本项目量价计算。",
                "noteEn": "iWencai returned no usable candidates; fell back to in-project price-volume computation.",
                "queries": queries,
            }
        )

    if errors:
        status["errors"] = errors[:5]
    return candidates, status


def fetch_spot_universe() -> list[dict[str, Any]]:
    fields = spot_fields()
    params = {
        "pn": 1,
        "pz": PAGE_SIZE,
        "po": 1,
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": A_SHARE_FS,
        "fields": fields,
    }
    first = request_json(EASTMONEY_QUOTE_API, params)
    data = first.get("data") or {}
    total = int(data.get("total") or 0)
    rows = list(data.get("diff") or [])

    for page in range(2, math.ceil(total / PAGE_SIZE) + 1):
        params["pn"] = page
        page_payload = request_json(EASTMONEY_QUOTE_API, params)
        page_rows = (page_payload.get("data") or {}).get("diff") or []
        rows.extend(page_rows)

    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = str(row.get("f12") or "").strip()
        if code:
            unique[code] = row
    return list(unique.values())


def spot_fields() -> str:
    return ",".join(
        [
            "f2",  # latest price
            "f3",  # pct change
            "f5",  # volume, lots
            "f6",  # amount, CNY
            "f8",  # turnover rate
            "f10",  # quote volume ratio
            "f12",  # code
            "f14",  # name
            "f15",  # high
            "f16",  # low
            "f17",  # open
            "f18",  # previous close
            "f100",  # industry
            "f102",  # region
            "f124",  # quote timestamp
        ]
    )


def fetch_spot_rows_for_codes(codes: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cleaned_codes = [code for code in dict.fromkeys(codes) if code]
    batch_size = 80

    for start in range(0, len(cleaned_codes), batch_size):
        batch = cleaned_codes[start : start + batch_size]
        secids = ",".join(secid_for_code(code) for code in batch)
        payload = request_json(
            "https://push2delay.eastmoney.com/api/qt/ulist.np/get",
            {
                "fltt": 2,
                "invt": 2,
                "fields": spot_fields(),
                "secids": secids,
            },
        )
        rows.extend((payload.get("data") or {}).get("diff") or [])

    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = str(row.get("f12") or "").strip()
        if code:
            unique[code] = row
    return list(unique.values())


def is_candidate(row: dict[str, Any]) -> bool:
    code = str(row.get("f12") or "").strip()
    name = str(row.get("f14") or "").strip()
    close = as_float(row.get("f2"))
    pct_change = as_float(row.get("f3"))
    amount = as_float(row.get("f6"))
    spot_volume_ratio = as_float(row.get("f10"))

    if not code or not name or close is None or pct_change is None or amount is None:
        return False
    if "ST" in name.upper() or name.startswith("*"):
        return False
    if pct_change <= MIN_PCT_CHANGE or amount < MIN_AMOUNT_CNY:
        return False
    if spot_volume_ratio is not None and spot_volume_ratio < MIN_SPOT_VOLUME_RATIO:
        return False
    if exchange_for_code(code) == "UNKNOWN":
        return False
    return True


def fetch_yahoo_klines(code: str, limit: int) -> list[dict[str, Any]]:
    payload = request_json(
        f"{YAHOO_CHART_API}/{urllib.parse.quote(yahoo_symbol_for_code(code))}",
        {
            "range": "1y",
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        },
    )
    result = ((payload.get("chart") or {}).get("result") or [None])[0]
    if not result:
        return []

    timestamps = result.get("timestamp") or []
    quote = (((result.get("indicators") or {}).get("quote") or [None])[0]) or {}
    opens = quote.get("open") or []
    closes = quote.get("close") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    volumes = quote.get("volume") or []
    rows = []

    for index, timestamp in enumerate(timestamps):
        open_price = as_float(opens[index] if index < len(opens) else None)
        close = as_float(closes[index] if index < len(closes) else None)
        high = as_float(highs[index] if index < len(highs) else None)
        low = as_float(lows[index] if index < len(lows) else None)
        volume_shares = as_float(volumes[index] if index < len(volumes) else None)
        if close is None or high is None or low is None or volume_shares is None:
            continue
        date = dt.datetime.fromtimestamp(int(timestamp), dt.timezone.utc).astimezone(
            market_now().tzinfo,
        ).date().isoformat()
        previous_close = rows[-1]["close"] if rows else None
        pct_change = None
        price_change = None
        if previous_close:
            price_change = close - float(previous_close)
            pct_change = (close / float(previous_close) - 1) * 100

        rows.append(
            {
                "date": date,
                "open": open_price,
                "close": close,
                "high": high,
                "low": low,
                "volume": int(volume_shares / 100),
                "amount": None,
                "amplitude": None,
                "pct_change": pct_change,
                "price_change": price_change,
                "turnover": None,
            }
        )

    return rows[-limit:]


def fetch_eastmoney_klines(code: str, limit: int) -> list[dict[str, Any]]:
    payload = request_json(
        EASTMONEY_KLINE_API,
        {
            "secid": secid_for_code(code),
            "klt": 101,
            "fqt": 1,
            "lmt": limit,
            "end": "20500101",
            "iscca": 1,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        },
    )
    klines = ((payload.get("data") or {}).get("klines")) or []
    parsed = []

    for line in klines:
        parts = str(line).split(",")
        if len(parts) < 11:
            continue
        volume = as_int(parts[5])
        amount = as_float(parts[6])
        turnover = as_float(parts[10])
        values = {
            "date": parts[0],
            "open": as_float(parts[1]),
            "close": as_float(parts[2]),
            "high": as_float(parts[3]),
            "low": as_float(parts[4]),
            "volume": volume,
            "amount": amount,
            "amplitude": as_float(parts[7]),
            "pct_change": as_float(parts[8]),
            "price_change": as_float(parts[9]),
            "turnover": turnover,
        }
        if values["close"] is None or values["high"] is None or volume is None:
            continue
        parsed.append(values)

    return parsed


def fetch_klines(code: str, limit: int) -> list[dict[str, Any]]:
    try:
        yahoo_rows = fetch_yahoo_klines(code, limit)
        if yahoo_rows:
            return yahoo_rows
    except Exception:
        pass

    return fetch_eastmoney_klines(code, limit)


def window_description(days: int) -> tuple[str, str]:
    if days == 1:
        return "超短线窗口：观察当日是否突破前一交易日高点", "Ultra-short window: close above the prior session high."
    if days in (2, 3):
        return f"超短线窗口：观察当日是否突破过去 {days} 个交易日高点", f"Ultra-short window: close above the prior {days} sessions."
    if days <= 20:
        return "短线窗口：观察约一个交易月内的前高突破", "Short-term window: roughly one trading month."
    if days <= 60:
        return "中线窗口：观察约一个季度内的前高突破", "Medium-term window: roughly one trading quarter."
    return "中长期窗口：观察约半年内的前高突破", "Mid-to-long-term window: roughly half a trading year."


def build_reason(
    row: dict[str, Any],
    latest: dict[str, Any],
    window_days: int,
    previous_high: float,
    average_volume: float,
    volume_ratio: float,
    breakout_pct: float,
    ths_candidate: dict[str, Any] | None,
    catalyst_bundle: dict[str, Any],
) -> tuple[str, str, list[dict[str, str]], list[str]]:
    code = str(row.get("f12"))
    name = str(row.get("f14"))
    industry = str(row.get("f100") or "未分类")
    region = str(row.get("f102") or "")
    close = float(latest["close"])
    pct_change = float(latest.get("pct_change") or row.get("f3") or 0)
    amount = float(latest.get("amount") or row.get("f6") or 0)
    turnover = latest.get("turnover")
    if turnover is None:
        turnover = as_float(row.get("f8"))
    volume = float(latest["volume"])

    tags = [industry]
    if region:
        tags.append(region)
    if volume_ratio >= 3:
        tags.append("高量能")
    elif volume_ratio >= 2.2:
        tags.append("明显放量")
    if pct_change >= 9.5:
        tags.append("接近涨停")
    if breakout_pct >= 3:
        tags.append("强突破")
    if window_days <= 3:
        tags.append("超短线突破")
    elif window_days >= 120:
        tags.append("中长期突破")
    elif window_days >= 60:
        tags.append("中线突破")
    else:
        tags.append("短线突破")
    ths_signals = []
    ths_queries = []
    if ths_candidate:
        ths_signals = list(dict.fromkeys(str(item) for item in ths_candidate.get("signals", []) if item))[:6]
        ths_queries = list(dict.fromkeys(str(item) for item in ths_candidate.get("queries", []) if item))[:3]
        tags.append("同花顺问财候选")
        for signal in ths_signals[:3]:
            if signal not in tags:
                tags.append(signal)
    for catalyst in catalyst_bundle.get("catalysts", [])[:3]:
        catalyst_type = str(catalyst.get("catalystTypeZh") or "")
        if catalyst_type and catalyst_type not in tags:
            tags.append(catalyst_type)

    turnover_text_zh = "换手率缺失" if turnover is None else f"换手率 {turnover:.2f}%"
    turnover_text_en = "turnover rate unavailable" if turnover is None else f"{turnover:.2f}% turnover rate"
    ths_reason_zh = (
        f"该股同时命中同花顺问财候选（{ ' / '.join(ths_queries) }），问财公开标签包括：{ ' / '.join(ths_signals) }；"
        if ths_signals and ths_queries
        else ""
    )
    ths_reason_en = (
        f"It also appeared in Tonghuashun iWencai candidate screens ({' / '.join(ths_queries)}), with public tags including {' / '.join(ths_signals)}. "
        if ths_signals and ths_queries
        else ""
    )

    reason_zh = (
        f"量价确认：{name}（{code}）收盘价 {close:.2f} 元，高于过去 {window_days} 个交易日最高价 "
        f"{previous_high:.2f} 元，突破幅度 {breakout_pct:.2f}%。当日成交量为窗口均量的 "
        f"{volume_ratio:.2f} 倍，成交额约 {amount / 100_000_000:.2f} 亿元，{turnover_text_zh}。"
        f"{ths_reason_zh}"
        "该部分只说明入选的交易条件，真正的消息/基本面催化需以上方公开来源为准。"
    )
    reason_en = (
        f"Price-volume confirmation: {name} ({code}) closed at CNY {close:.2f}, above the previous {window_days}-session high "
        f"of CNY {previous_high:.2f}, a {breakout_pct:.2f}% breakout. Volume was {volume_ratio:.2f}x "
        f"the window average, value traded was about CNY {amount / 1_000_000_000:.2f}bn, with "
        f"{turnover_text_en}. {ths_reason_en}This confirms the screening condition only; the public-source "
        "catalyst section above should be used for fundamental/news verification."
    )

    factors = [
        {
            "labelZh": "价格位置",
            "labelEn": "Price position",
            "valueZh": f"收盘 {close:.2f} / 前高 {previous_high:.2f}",
            "valueEn": f"Close {close:.2f} / prior high {previous_high:.2f}",
        },
        {
            "labelZh": "放量程度",
            "labelEn": "Volume expansion",
            "valueZh": f"{volume_ratio:.2f} 倍；成交量 {volume:,.0f} 手",
            "valueEn": f"{volume_ratio:.2f}x; {volume:,.0f} lots",
        },
        {
            "labelZh": "资金活跃度",
            "labelEn": "Trading activity",
            "valueZh": f"成交额 {amount / 100_000_000:.2f} 亿元；{turnover_text_zh}",
            "valueEn": f"CNY {amount / 1_000_000_000:.2f}bn traded; {turnover_text_en}",
        },
        {
            "labelZh": "板块背景",
            "labelEn": "Sector context",
            "valueZh": f"{industry}{f' / {region}' if region else ''}",
            "valueEn": f"{industry}{f' / {region}' if region else ''}",
        },
    ]
    if ths_signals or ths_queries:
        factors.append(
            {
                "labelZh": "候选来源",
                "labelEn": "Candidate source",
                "valueZh": f"同花顺问财：{' / '.join(ths_signals[:4]) if ths_signals else '候选命中'}",
                "valueEn": f"Tonghuashun iWencai: {' / '.join(ths_signals[:4]) if ths_signals else 'candidate match'}",
            }
        )
    factors.append(
        {
            "labelZh": "消息催化",
            "labelEn": "News catalyst",
            "valueZh": catalyst_bundle.get("summaryZh", "未找到可核验催化")[:96],
            "valueEn": catalyst_bundle.get("summaryEn", "No verified catalyst found")[:120],
        }
    )

    return reason_zh, reason_en, factors, tags


def analyze_stock(
    row: dict[str, Any],
    limit: int,
    ths_candidates: dict[str, dict[str, Any]],
) -> tuple[str | None, list[dict[str, Any]]]:
    code = str(row.get("f12") or "")
    ths_candidate = ths_candidates.get(code)
    klines = fetch_klines(code, limit)
    if not klines:
        return None, []

    latest = klines[-1]
    latest_date = str(latest["date"])
    catalyst_bundle = build_catalyst_bundle(row, latest_date, ths_candidate)
    results = []

    for window_days in WINDOWS:
        if len(klines) < window_days + 1:
            continue
        history = klines[-window_days - 1 : -1]
        previous_high = max(float(item["high"]) for item in history)
        close = float(latest["close"])
        latest_high = float(latest["high"])
        latest_volume = float(latest["volume"])
        volumes = [float(item["volume"]) for item in history if item.get("volume")]
        if not volumes or previous_high <= 0:
            continue

        average_volume = statistics.fmean(volumes)
        volume_ratio = latest_volume / average_volume if average_volume > 0 else 0
        breakout_pct = (close / previous_high - 1) * 100
        amount = float(latest.get("amount") or row.get("f6") or 0)
        turnover = latest.get("turnover")
        if turnover is None:
            turnover = as_float(row.get("f8"))
        pct_change = float(latest.get("pct_change") or row.get("f3") or 0)

        if close <= previous_high:
            continue
        if breakout_pct <= MIN_BREAKOUT_PCT:
            continue
        if volume_ratio < MIN_VOLUME_RATIO:
            continue
        if turnover is not None and float(turnover) < MIN_TURNOVER_RATE:
            continue
        if amount < MIN_AMOUNT_CNY or pct_change <= MIN_PCT_CHANGE:
            continue

        reason_zh, reason_en, factors, tags = build_reason(
            row,
            latest,
            window_days,
            previous_high,
            average_volume,
            volume_ratio,
            breakout_pct,
            ths_candidate,
            catalyst_bundle,
        )
        rank_score = (
            volume_ratio * 2.0
            + breakout_pct * 1.2
            + pct_change * 0.25
            + max(math.log10(max(amount, 1) / 100_000_000), 0) * 0.8
            + (float(turnover or 0) * 0.12)
        )

        results.append(
            {
                "code": code,
                "name": str(row.get("f14") or ""),
                "exchange": exchange_for_code(code),
                "market": "CN",
                "quoteUrl": quote_url_for_code(code),
                "industry": str(row.get("f100") or ""),
                "region": str(row.get("f102") or ""),
                "tradeDate": latest_date,
                "windowDays": window_days,
                "close": round(close, 4),
                "high": round(latest_high, 4),
                "previousHigh": round(previous_high, 4),
                "breakoutPct": round(breakout_pct, 4),
                "pctChange": round(pct_change, 4),
                "volume": int(latest_volume),
                "averageVolume": round(average_volume, 2),
                "volumeRatio": round(volume_ratio, 4),
                "amountCny": round(amount, 2),
                "turnoverRate": None if turnover is None else round(float(turnover), 4),
                "rankScore": round(rank_score, 4),
                "tags": tags,
                "candidateSources": (
                    ["同花顺问财候选 / Tonghuashun iWencai", "本项目量价校验 / In-project validation"]
                    if ths_candidate
                    else ["本项目量价筛选 / In-project screening"]
                ),
                "externalSignals": (
                    [
                        {
                            "sourceZh": "同花顺问财",
                            "sourceEn": "Tonghuashun iWencai",
                            "queries": ths_candidate.get("queries", []),
                            "signals": ths_candidate.get("signals", [])[:10],
                            "noteZh": "仅使用问财候选与标签作辅助线索；突破、放量、成交额、换手由本项目重新计算校验。",
                            "noteEn": "Only candidate membership and tags are used as auxiliary signals; breakout, volume, traded value, and turnover are re-computed by this project.",
                        }
                    ]
                    if ths_candidate
                    else []
                ),
                "fundamentalCatalystStatus": catalyst_bundle["status"],
                "fundamentalSummaryZh": catalyst_bundle["summaryZh"],
                "fundamentalSummaryEn": catalyst_bundle["summaryEn"],
                "industryWatchZh": catalyst_bundle["industryWatchZh"],
                "industryWatchEn": catalyst_bundle["industryWatchEn"],
                "fundamentalCatalysts": catalyst_bundle["catalysts"],
                "reasonZh": reason_zh,
                "reasonEn": reason_en,
                "factors": factors,
            }
        )

    return latest_date, results


def build_report(
    rows: list[dict[str, Any]],
    max_workers: int,
    max_candidates: int | None,
    candidate_provider: CandidateProvider,
    ths_candidates: dict[str, dict[str, Any]],
    ths_status: dict[str, Any],
    used_fallback_universe: bool,
) -> dict[str, Any]:
    computed_candidates = [row for row in rows if is_candidate(row)]

    row_by_code = {str(row.get("f12") or ""): row for row in rows}
    if candidate_provider == "ths":
        candidates = [row_by_code[code] for code in ths_candidates if code in row_by_code]
        if not candidates:
            candidates = computed_candidates
            ths_status["noteZh"] = f"{ths_status.get('noteZh', '')} 未找到可复核的问财候选，已回退到本项目量价预筛。"
            ths_status["noteEn"] = f"{ths_status.get('noteEn', '')} No re-validatable iWencai candidates were found; fell back to in-project prefiltering."
    elif candidate_provider == "hybrid":
        if ths_candidates and not used_fallback_universe:
            candidates = [row_by_code[code] for code in ths_candidates if code in row_by_code]
        else:
            candidates = computed_candidates
    else:
        candidates = computed_candidates

    if max_candidates is not None:
        candidates = candidates[:max_candidates]

    limit = max(WINDOWS) + 8
    by_window: dict[int, list[dict[str, Any]]] = {window: [] for window in WINDOWS}
    trade_dates: list[str] = []
    failures = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_stock, row, limit, ths_candidates): row for row in candidates}
        for future in concurrent.futures.as_completed(futures):
            try:
                trade_date, results = future.result()
            except Exception:
                failures += 1
                continue
            if trade_date:
                trade_dates.append(trade_date)
            for result in results:
                by_window[int(result["windowDays"])].append(result)

    trade_date = max(trade_dates) if trade_dates else market_now().date().isoformat()

    windows = []
    for days in WINDOWS:
        description_zh, description_en = window_description(days)
        stocks = [
            stock
            for stock in by_window[days]
            if stock["tradeDate"] == trade_date
        ]
        stocks.sort(key=lambda item: item["rankScore"], reverse=True)
        windows.append(
            {
                "days": days,
                "labelZh": f"{days} 日窗口",
                "labelEn": f"{days}-day window",
                "descriptionZh": description_zh,
                "descriptionEn": description_en,
                "stocks": stocks,
            }
        )

    generated_at = market_now().isoformat(timespec="seconds")
    catalyst_codes = {
        stock["code"]
        for window in windows
        for stock in window["stocks"]
        if stock.get("fundamentalCatalysts")
    }
    return {
        "schemaVersion": 2,
        "generatedAt": generated_at,
        "tradeDate": trade_date,
        "source": {
            "name": "同花顺问财候选 + 东方财富公告/资讯 + 东方财富/Yahoo 量价校验 / iWencai + Eastmoney catalysts + market validation",
            "url": THS_WENCAI_URL if candidate_provider in ("hybrid", "ths") else EASTMONEY_QUOTE_BASE,
            "noteZh": "候选源优先接入同花顺问财；公告和新闻标题来自东方财富公开接口；行情列表来自东方财富 push2delay，日 K 优先来自 Yahoo Finance，若 Yahoo 不可用则回退到东方财富 push2his。基本面催化只作为可核验线索，不单独证明上涨因果。",
            "noteEn": "Candidate sourcing prefers Tonghuashun iWencai. Announcement/news titles come from public Eastmoney endpoints. Quote lists come from Eastmoney push2delay, daily candles prefer Yahoo Finance and fall back to Eastmoney push2his. Fundamental catalysts are verification leads, not proof of causality.",
        },
        "scopeZh": "hybrid 模式优先使用同花顺问财候选，再按统一口径复核 1/2/3/20/60/120 日窗口；问财不可用时回退到本项目全市场量价预筛。当前覆盖东方财富沪深 A 股行情集合，包括沪深主板、创业板、科创板。",
        "scopeEn": "Hybrid mode prioritizes Tonghuashun iWencai candidates, then re-validates 1/2/3/20/60/120-day windows with one consistent rule set; if iWencai is unavailable it falls back to the in-project full-universe price-volume prefilter. Current coverage is the Eastmoney Shanghai/Shenzhen A-share universe.",
        "candidateProvider": candidate_provider,
        "providerStatuses": [
            ths_status,
            {
                "id": "computed-prefilter",
                "nameZh": "本项目量价预筛",
                "nameEn": "In-project price-volume prefilter",
                "status": "ok",
                "count": len(computed_candidates),
                "noteZh": (
                    f"本项目在问财候选范围内预筛命中 {len(computed_candidates)} 只；最终结果仍需通过窗口前高和窗口均量复核。"
                    if ths_candidates and not used_fallback_universe
                    else f"本项目全市场预筛返回 {len(computed_candidates)} 只候选；最终结果仍需通过窗口前高和窗口均量复核。"
                ),
                "noteEn": (
                    f"The in-project prefilter matched {len(computed_candidates)} names within the iWencai candidate set; final results still require prior-high and average-volume validation."
                    if ths_candidates and not used_fallback_universe
                    else f"The in-project full-universe prefilter returned {len(computed_candidates)} candidates; final results still require prior-high and average-volume validation."
                ),
                "queries": [],
            },
            {
                "id": "eastmoney-catalysts",
                "nameZh": "东方财富公告/资讯催化",
                "nameEn": "Eastmoney announcement/news catalysts",
                "status": "ok",
                "count": len(catalyst_codes),
                "noteZh": f"近 {CATALYST_LOOKBACK_DAYS} 天公告/新闻标题中，为 {len(catalyst_codes)} 只入选股票找到可展示的基本面或市场催化线索；未找到时会明确提示继续核验。",
                "noteEn": f"Announcement/news titles within {CATALYST_LOOKBACK_DAYS} days produced displayable fundamental or market catalyst leads for {len(catalyst_codes)} qualified stocks; missing evidence is shown explicitly.",
                "queries": [],
            },
        ],
        "criteria": [
            {
                "key": "breakoutBasis",
                "labelZh": "突破口径",
                "labelEn": "Breakout basis",
                "value": "收盘价 > 所选窗口前高 / Close above prior window high",
            },
            {
                "key": "minimumVolumeRatio",
                "labelZh": "最低放量",
                "labelEn": "Minimum volume expansion",
                "value": f"{MIN_VOLUME_RATIO:.1f}x",
            },
            {
                "key": "spotPrefilterVolumeRatio",
                "labelZh": "列表预过滤量比",
                "labelEn": "Spot prefilter volume ratio",
                "value": f"{MIN_SPOT_VOLUME_RATIO:.1f}x",
            },
            {
                "key": "minimumAmount",
                "labelZh": "最低成交额",
                "labelEn": "Minimum value traded",
                "value": f"¥{MIN_AMOUNT_CNY / 100_000_000:.1f} 亿 / CNY {MIN_AMOUNT_CNY / 1_000_000:.0f}m",
            },
            {
                "key": "minimumTurnover",
                "labelZh": "最低换手",
                "labelEn": "Minimum turnover rate",
                "value": f"{MIN_TURNOVER_RATE:.1f}%",
            },
        ],
        "disclaimerZh": f"本次以 {candidate_provider} 模式扫描候选 {len(candidates)} 只，K 线失败 {failures} 只；问财只作候选与标签线索，最终入选由本项目量价口径复核；公告/新闻催化只表示可核验线索，不构成因果证明或投资建议。",
        "disclaimerEn": f"Scanned {len(candidates)} candidates in {candidate_provider} mode with {failures} candle failures. iWencai is used only for candidate and tag hints; final inclusion is re-validated by this project's price-volume rules. Announcement/news catalysts are verification leads, not causality proof or investment advice.",
        "windows": windows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-workers", type=int, default=18)
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument(
        "--candidate-provider",
        choices=("computed", "hybrid", "ths"),
        default="hybrid",
        help="Candidate source strategy. hybrid uses iWencai candidates plus in-project prefiltering.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ths_candidates: dict[str, dict[str, Any]] = {}
    ths_status = {
        "id": "ths-wencai",
        "nameZh": "同花顺问财候选",
        "nameEn": "Tonghuashun iWencai candidates",
        "status": "skipped",
        "count": 0,
        "noteZh": "当前模式未启用同花顺问财候选源。",
        "noteEn": "Tonghuashun iWencai candidate source was not enabled in this mode.",
        "queries": [],
    }
    used_fallback_universe = False

    if args.candidate_provider in ("hybrid", "ths"):
        ths_candidates, ths_status = fetch_ths_wencai_candidates(WINDOWS)

    if args.candidate_provider in ("hybrid", "ths") and ths_candidates:
        rows = fetch_spot_rows_for_codes(list(ths_candidates.keys()))
        if not rows:
            rows = fetch_spot_universe()
            used_fallback_universe = True
            ths_status["noteZh"] = f"{ths_status.get('noteZh', '')} 候选行情补全失败，已回退到全市场量价预筛。"
            ths_status["noteEn"] = f"{ths_status.get('noteEn', '')} Candidate quote enrichment failed; fell back to the full-universe prefilter."
    else:
        rows = fetch_spot_universe()
        used_fallback_universe = args.candidate_provider in ("hybrid", "ths")

    report = build_report(
        rows,
        max_workers=max(1, args.max_workers),
        max_candidates=args.max_candidates,
        candidate_provider=args.candidate_provider,
        ths_candidates=ths_candidates,
        ths_status=ths_status,
        used_fallback_universe=used_fallback_universe,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = ", ".join(f"{window['days']}d={len(window['stocks'])}" for window in report["windows"])
    output_name = args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output
    print(f"Wrote {output_name} for {report['tradeDate']} ({counts})")


if __name__ == "__main__":
    main()
