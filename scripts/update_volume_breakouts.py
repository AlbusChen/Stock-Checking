#!/usr/bin/env python3
"""Refresh daily A-share volume breakout candidates for the static app."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
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
YAHOO_CHART_API = "https://query1.finance.yahoo.com/v8/finance/chart"
EASTMONEY_QUOTE_BASE = "https://quote.eastmoney.com"
THS_WENCAI_URL = "https://www.iwencai.com"
A_SHARE_FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
WINDOWS = (20, 60, 120)
PAGE_SIZE = 100
MIN_AMOUNT_CNY = 50_000_000
MIN_TURNOVER_RATE = 1.0
MIN_VOLUME_RATIO = 1.8
MIN_SPOT_VOLUME_RATIO = 1.5
MIN_PCT_CHANGE = 0.0
MIN_BREAKOUT_PCT = 0.0
REQUEST_TIMEOUT = 16
THS_QUERY_TIMEOUT = 35
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Stock-Checking/1.0 Safari/537.36"
)

CandidateProvider = str


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
    queries = [f"今日{days}日放量突破" for days in windows]

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
    if window_days >= 120:
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
        f"{name}（{code}）收盘价 {close:.2f} 元，高于过去 {window_days} 个交易日最高价 "
        f"{previous_high:.2f} 元，突破幅度 {breakout_pct:.2f}%。当日成交量为窗口均量的 "
        f"{volume_ratio:.2f} 倍，成交额约 {amount / 100_000_000:.2f} 亿元，{turnover_text_zh}。"
        f"{ths_reason_zh}"
        f"量价同步放大，行业字段为“{industry}”，更像资金围绕该板块或个股趋势做突破确认；"
        "该判断基于行情数据，不等同于已确认公告利好。"
    )
    reason_en = (
        f"{name} ({code}) closed at CNY {close:.2f}, above the previous {window_days}-session high "
        f"of CNY {previous_high:.2f}, a {breakout_pct:.2f}% breakout. Volume was {volume_ratio:.2f}x "
        f"the window average, value traded was about CNY {amount / 1_000_000_000:.2f}bn, with "
        f"{turnover_text_en}. {ths_reason_en}The move looks like a price-volume confirmation around the stock or "
        f"its {industry} industry tag, not a verified announcement-driven catalyst."
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
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "tradeDate": trade_date,
        "source": {
            "name": "同花顺问财候选 + 东方财富/Yahoo 量价校验 / iWencai candidates + Eastmoney/Yahoo validation",
            "url": THS_WENCAI_URL if candidate_provider in ("hybrid", "ths") else EASTMONEY_QUOTE_BASE,
            "noteZh": "候选源优先接入同花顺问财；行情列表来自东方财富 push2delay 延迟行情公开接口，日 K 优先来自 Yahoo Finance A 股历史行情，若 Yahoo 不可用则回退到东方财富 push2his。原因分析由本项目按公开量价字段自动生成。",
            "noteEn": "Candidate sourcing prefers Tonghuashun iWencai. The quote list comes from Eastmoney delayed push2delay, daily candles prefer Yahoo Finance A-share history and fall back to Eastmoney push2his. Analysis text is generated by this project from public price-volume fields.",
        },
        "scopeZh": "hybrid 模式优先使用同花顺问财候选，再按统一口径复核 20/60/120 日窗口；问财不可用时回退到本项目全市场量价预筛。当前覆盖东方财富沪深 A 股行情集合，包括沪深主板、创业板、科创板。",
        "scopeEn": "Hybrid mode prioritizes Tonghuashun iWencai candidates, then re-validates 20/60/120-day windows with one consistent rule set; if iWencai is unavailable it falls back to the in-project full-universe price-volume prefilter. Current coverage is the Eastmoney Shanghai/Shenzhen A-share universe.",
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
        "disclaimerZh": f"本次以 {candidate_provider} 模式扫描候选 {len(candidates)} 只，K 线失败 {failures} 只；问财只作候选与标签线索，最终入选由本项目量价口径复核，不构成投资建议。",
        "disclaimerEn": f"Scanned {len(candidates)} candidates in {candidate_provider} mode with {failures} candle failures. iWencai is used only for candidate and tag hints; final inclusion is re-validated by this project's price-volume rules and is not investment advice.",
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
